"""
Forms pour l'interface web de production vidéo.
Architecture flexible, validation dynamique.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models_extended import (
    VideoProductionJob,
    VideoProjectTemplate,
    SegmentAsset,
    VideoGenerationMode,
    VideoProvider,
    ContentPillar
)
import json


class VideoProjectTemplateForm(forms.ModelForm):
    """Form pour créer/éditer un template"""
    
    # Config fields (extraits du JSON pour UX)
    default_provider = forms.ChoiceField(
        choices=VideoProvider.choices,
        initial=VideoProvider.LUMA,
        label="Provider par défaut"
    )
    
    default_mode = forms.ChoiceField(
        choices=VideoGenerationMode.choices,
        initial=VideoGenerationMode.TEXT_TO_VIDEO,
        label="Mode par défaut"
    )
    
    default_aspect_ratio = forms.ChoiceField(
        choices=[
            ('9:16', 'Vertical (TikTok/Reels)'),
            ('16:9', 'Horizontal (YouTube)'),
            ('1:1', 'Carré (Instagram)')
        ],
        initial='9:16',
        label="Format"
    )
    
    class Meta:
        model = VideoProjectTemplate
        fields = [
            'name', 
            'description', 
            'pillar',
            'segments_count',
            'segment_duration',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'segments_count': forms.NumberInput(attrs={'min': 1, 'max': 20}),
            'segment_duration': forms.NumberInput(attrs={'min': 3, 'max': 10}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Build default_config from extracted fields
        instance.default_config = {
            'provider': self.cleaned_data['default_provider'],
            'mode': self.cleaned_data['default_mode'],
            'aspect_ratio': self.cleaned_data['default_aspect_ratio'],
        }
        
        if commit:
            instance.save()
        return instance


class VideoProductionJobForm(forms.ModelForm):
    """
    Form principal pour créer un job de production.
    Supporte tous les modes (text/image/video-to-video).
    """
    
    # Override provider/mode (optionnel, sinon template)
    override_provider = forms.ChoiceField(
        choices=[('', 'Utiliser template')] + list(VideoProvider.choices),
        required=False,
        label="Provider (override)"
    )
    
    override_mode = forms.ChoiceField(
        choices=[('', 'Utiliser template')] + list(VideoGenerationMode.choices),
        required=False,
        label="Mode (override)"
    )
    
    # Script manual override
    use_manual_script = forms.BooleanField(
        required=False,
        initial=False,
        label="Écrire le script manuellement (skip IA)"
    )
    
    class Meta:
        model = VideoProductionJob
        fields = [
            'title',
            'theme',
            'template',
            'script_text',
        ]
        widgets = {
            'theme': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'Ex: Django tips pour débutants - créer une app en 5 minutes'
            }),
            'script_text': forms.Textarea(attrs={
                'rows': 10,
                'placeholder': 'Script voix-off (optionnel si génération IA)'
            }),
            'template': forms.Select(attrs={
                'class': 'template-selector'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        template = cleaned_data.get('template')
        use_manual = cleaned_data.get('use_manual_script')
        script = cleaned_data.get('script_text')
        
        # Si manual script, vérifier qu'il est fourni
        if use_manual and not script:
            raise ValidationError(
                "Script manuel requis si 'use_manual_script' est activé"
            )
        
        # Build config dict
        config = {}
        
        if cleaned_data.get('override_provider'):
            config['provider'] = cleaned_data['override_provider']
        
        if cleaned_data.get('override_mode'):
            config['mode'] = cleaned_data['override_mode']
        
        cleaned_data['config'] = config
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Injecter config
        instance.config = self.cleaned_data.get('config', {})
        
        # Calculer coût estimé
        instance.calculate_estimated_cost()
        
        # Si script manuel fourni, skip script generation
        if self.cleaned_data.get('use_manual_script'):
            instance.status = VideoProductionJob.Status.SCRIPT_READY
        else:
            instance.status = VideoProductionJob.Status.DRAFT
        
        if commit:
            instance.save()
        
        return instance


class SegmentAssetUploadForm(forms.ModelForm):
    """
    Upload d'asset pour un segment (image-to-video).
    Utilisé dans l'interface de configuration segments.
    """
    
    class Meta:
        model = SegmentAsset
        fields = [
            'segment_index',
            'asset_type',
            'file',
            'url',
            'animation_prompt',
        ]
        widgets = {
            'animation_prompt': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Ex: Le curseur tape le code, zoom sur la fonction, terminal exécute la commande...'
            }),
            'segment_index': forms.NumberInput(attrs={'min': 0}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('file')
        url = cleaned_data.get('url')
        
        # Au moins un des deux
        if not file and not url:
            raise ValidationError(
                "Fournir soit un fichier uploadé, soit une URL"
            )
        
        # Pas les deux
        if file and url:
            raise ValidationError(
                "Choisir soit fichier, soit URL (pas les deux)"
            )
        
        return cleaned_data


class BulkSegmentConfigForm(forms.Form):
    """
    Configuration en masse des segments d'un job.
    Permet de définir prompts + assets pour chaque segment.
    """
    
    def __init__(self, *args, job=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not job:
            return
        
        segments_count = job.get_config('segments_count', 6)
        
        # Générer fields dynamiquement pour chaque segment
        for i in range(segments_count):
            # Prompt
            self.fields[f'segment_{i}_prompt'] = forms.CharField(
                label=f'Segment {i+1} - Prompt',
                widget=forms.Textarea(attrs={
                    'rows': 2,
                    'placeholder': 'Description visuelle du segment...'
                }),
                required=True
            )
            
            # Asset (optionnel)
            self.fields[f'segment_{i}_asset'] = forms.FileField(
                label=f'Segment {i+1} - Image de référence (optionnel)',
                required=False,
                help_text='Upload image pour mode image-to-video'
            )
            
            # Animation prompt (si asset fourni)
            self.fields[f'segment_{i}_animation'] = forms.CharField(
                label=f'Segment {i+1} - Animation',
                widget=forms.Textarea(attrs={
                    'rows': 1,
                    'placeholder': 'Comment animer cette image...'
                }),
                required=False
            )
    
    def get_segments_data(self):
        """
        Retourne liste structurée des configs segments.
        [{
            'index': 0,
            'prompt': '...',
            'asset': FileObject,
            'animation_prompt': '...'
        }, ...]
        """
        if not self.is_valid():
            return []
        
        segments = []
        i = 0
        
        while f'segment_{i}_prompt' in self.cleaned_data:
            segment_data = {
                'index': i,
                'prompt': self.cleaned_data[f'segment_{i}_prompt'],
                'asset': self.cleaned_data.get(f'segment_{i}_asset'),
                'animation_prompt': self.cleaned_data.get(f'segment_{i}_animation', ''),
            }
            segments.append(segment_data)
            i += 1
        
        return segments


class QuickVideoForm(forms.Form):
    """
    Form rapide "one-shot" pour générer vidéo sans passer par job complet.
    Utile pour tests ou génération simple.
    """
    
    theme = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={
            'rows': 2,
            'placeholder': 'Ex: Python tip - list comprehensions'
        }),
        label="Sujet"
    )
    
    pillar = forms.ChoiceField(
        choices=ContentPillar.choices,
        initial=ContentPillar.TIPS,
        label="Type de contenu"
    )
    
    provider = forms.ChoiceField(
        choices=VideoProvider.choices,
        initial=VideoProvider.LUMA,
        label="Provider vidéo"
    )
    
    mode = forms.ChoiceField(
        choices=VideoGenerationMode.choices,
        initial=VideoGenerationMode.TEXT_TO_VIDEO,
        label="Mode génération"
    )
    
    segments_count = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=6,
        label="Nombre de segments"
    )
    
    segment_duration = forms.IntegerField(
        min_value=3,
        max_value=10,
        initial=5,
        label="Durée par segment (sec)"
    )
    
    aspect_ratio = forms.ChoiceField(
        choices=[
            ('9:16', 'Vertical (TikTok/Reels)'),
            ('16:9', 'Horizontal (YouTube)'),
            ('1:1', 'Carré (Instagram)')
        ],
        initial='9:16',
        label="Format"
    )
    
    def create_job(self, user=None):
        """
        Crée un VideoProductionJob à partir du form.
        Helper pour quick generation.
        """
        if not self.is_valid():
            return None
        
        data = self.cleaned_data
        
        # Créer config
        config = {
            'provider': data['provider'],
            'mode': data['mode'],
            'segments_count': data['segments_count'],
            'segment_duration': data['segment_duration'],
            'aspect_ratio': data['aspect_ratio'],
        }
        
        # Créer job
        job = VideoProductionJob.objects.create(
            title=f"Quick: {data['theme'][:50]}",
            theme=data['theme'],
            config=config,
            created_by=user,
            status=VideoProductionJob.Status.DRAFT
        )
        
        job.calculate_estimated_cost()
        job.save()
        
        return job
