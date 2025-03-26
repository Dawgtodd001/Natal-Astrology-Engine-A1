from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ApiKey(Base):
    """API key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    enabled = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # Requests per day
    
    def __repr__(self):
        return f"<ApiKey {self.name}>"


class PlanetInterpretation(Base):
    """Interpretation for planet in sign combinations"""
    __tablename__ = "planet_interpretations"
    
    id = Column(Integer, primary_key=True, index=True)
    planet = Column(String(20), nullable=False, index=True)
    sign = Column(String(20), nullable=False, index=True)
    interpretation = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<PlanetInterpretation {self.planet} in {self.sign}>"


class HouseInterpretation(Base):
    """Interpretation for planets in houses"""
    __tablename__ = "house_interpretations"
    
    id = Column(Integer, primary_key=True, index=True)
    planet = Column(String(20), nullable=False, index=True)
    house = Column(Integer, nullable=False, index=True)
    interpretation = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<HouseInterpretation {self.planet} in house {self.house}>"


class AspectInterpretation(Base):
    """Interpretation for aspects between planets"""
    __tablename__ = "aspect_interpretations"
    
    id = Column(Integer, primary_key=True, index=True)
    planet1 = Column(String(20), nullable=False, index=True)
    planet2 = Column(String(20), nullable=False, index=True)
    aspect_type = Column(String(20), nullable=False, index=True)
    interpretation = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<AspectInterpretation {self.planet1} {self.aspect_type} {self.planet2}>"


class ChartCalculation(Base):
    """Record of chart calculations for caching and analytics"""
    __tablename__ = "chart_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    birth_date = Column(String(10), nullable=False)
    birth_time = Column(String(5), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=False)
    house_system = Column(String(20), default="placidus")
    zodiac_type = Column(String(20), default="tropical")
    calculation_timestamp = Column(String(26), nullable=False)
    
    def __repr__(self):
        return f"<ChartCalculation {self.birth_date} {self.birth_time}>"


class InterpretationTemplate(Base):
    """Templates for different output formats"""
    __tablename__ = "interpretation_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    format_type = Column(String(20), nullable=False)  # markdown, html, text
    template_content = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<InterpretationTemplate {self.name} ({self.format_type})>"
