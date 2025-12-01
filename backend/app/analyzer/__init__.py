"""Módulo de análise de texto com IA."""

from .ai_analyzer import BookAnalyzer
from .ollama_analyzer import OllamaAnalyzer
from .huggingface_analyzer import HuggingFaceAnalyzer
from .bedrock_analyzer import BedrockAnalyzer
from .gradio_analyzer import GradioAnalyzer

__all__ = ["BookAnalyzer", "OllamaAnalyzer", "HuggingFaceAnalyzer", "BedrockAnalyzer", "GradioAnalyzer"]


def get_analyzer(provider: str = "ollama", **kwargs):
    """
    Factory para criar o analisador apropriado.
    
    Args:
        provider: "ollama", "openai", "huggingface", "bedrock" ou "gradio"
        **kwargs: Argumentos para o analisador
        
    Returns:
        Instância do analisador
    """
    providers = {
        "ollama": OllamaAnalyzer,
        "openai": BookAnalyzer,
        "huggingface": HuggingFaceAnalyzer,
        "bedrock": BedrockAnalyzer,
        "gradio": GradioAnalyzer
    }
    
    if provider not in providers:
        raise ValueError(f"Provider '{provider}' não suportado. Use: {list(providers.keys())}")
    
    return providers[provider](**kwargs)

