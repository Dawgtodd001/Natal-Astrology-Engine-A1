from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import sqlalchemy

Base = declarative_base()

class ApiKey(Base):
    """API key model for authentication"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True)
    name = Column(String(128), nullable=False)
    enabled = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=60)  # Requests per minute
    daily_limit = Column(Integer, default=1000)  # Requests per day
    created_at = Column(String(26), nullable=True)
    last_used = Column(String(26), nullable=True)
    
    def __repr__(self):
        return f"<ApiKey {self.name}>"


class PlanetInterpretation(Base):
    """Interpretation for planet in sign combinations"""
    __tablename__ = "planet_interpretations"
    
    id = Column(Integer, primary_key=True, index=True)
    planet = Column(String(20), nullable=False, index=True)
    sign = Column(String(20), nullable=False, index=True)
    interpretation = Column(Text, nullable=False)
    
    # Composite index for faster lookups by planet-sign combination
    __table_args__ = (
        sqlalchemy.schema.Index('idx_planet_sign', 'planet', 'sign'),
    )
    
    def __repr__(self):
        return f"<PlanetInterpretation {self.planet} in {self.sign}>"


class HouseInterpretation(Base):
    """Interpretation for planets in houses"""
    __tablename__ = "house_interpretations"
    
    id = Column(Integer, primary_key=True, index=True)
    planet = Column(String(20), nullable=False, index=True)
    house = Column(Integer, nullable=False, index=True)
    interpretation = Column(Text, nullable=False)
    
    # Composite index for faster lookups by planet-house combination
    __table_args__ = (
        schema.Index('idx_planet_house', 'planet', 'house'),
    )
    
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
    
    # Composite index for faster lookups by planet1-planet2-aspect_type combination
    __table_args__ = (
        schema.Index('idx_planets_aspect', 'planet1', 'planet2', 'aspect_type'),
    )
    
    def __repr__(self):
        return f"<AspectInterpretation {self.planet1} {self.aspect_type} {self.planet2}>"


class ChartCalculation(Base):
    """Record of chart calculations for caching and analytics"""
    __tablename__ = "chart_calculations"
    
    id = Column(Integer, primary_key=True, index=True)
    birth_date = Column(String(10), nullable=False, index=True)
    birth_time = Column(String(5), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=False)
    house_system = Column(String(20), default="placidus", index=True)
    zodiac_type = Column(String(20), default="tropical", index=True)
    calculation_timestamp = Column(String(26), nullable=False, index=True)
    cache_key = Column(String(64), nullable=True, index=True, unique=True)
    result_json = Column(Text, nullable=True)
    
    # Composite index for faster lookups by chart data
    __table_args__ = (
        schema.Index('idx_chart_params', 'birth_date', 'birth_time', 'house_system', 'zodiac_type'),
        schema.Index('idx_chart_timestamp', 'calculation_timestamp'),
    )
    
    def __repr__(self):
        return f"<ChartCalculation {self.birth_date} {self.birth_time}>"


class UserProfile(Base):
    """User profile for storing saved birth data"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    birth_date = Column(String(10), nullable=False)
    birth_time = Column(String(5), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timezone = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(String(26), nullable=False)
    
    def __repr__(self):
        return f"<UserProfile {self.name}: {self.birth_date} {self.birth_time}>"


class InterpretationTemplate(Base):
    """Templates for different output formats"""
    __tablename__ = "interpretation_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    format_type = Column(String(20), nullable=False)  # markdown, html, text
    template_content = Column(Text, nullable=False)
    
    def __repr__(self):
        return f"<InterpretationTemplate {self.name} ({self.format_type})>"
