"""Strategies module."""

from .standard import StandardRankStrategy
from .diversity import DiversityRankStrategy

__all__ = ["StandardRankStrategy", "DiversityRankStrategy"]