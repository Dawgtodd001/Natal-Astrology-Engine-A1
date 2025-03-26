import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{os.getenv('PGUSER')}:{os.getenv('PGPASSWORD')}@{os.getenv('PGHOST')}:{os.getenv('PGPORT')}/{os.getenv('PGDATABASE')}"
)

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Get a database session
    Used as a dependency in FastAPI endpoints
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database with tables and seed data"""
    from app.models import Base, PlanetInterpretation, HouseInterpretation, AspectInterpretation, InterpretationTemplate, ApiKey
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Add seed data if tables are empty
    db = SessionLocal()
    
    # Seed API keys if none exist
    if db.query(ApiKey).count() == 0:
        seed_api_keys(db)
    
    # Seed planet interpretations if none exist
    if db.query(PlanetInterpretation).count() == 0:
        seed_planet_interpretations(db)
    
    # Seed house interpretations if none exist
    if db.query(HouseInterpretation).count() == 0:
        seed_house_interpretations(db)
    
    # Seed aspect interpretations if none exist
    if db.query(AspectInterpretation).count() == 0:
        seed_aspect_interpretations(db)
        
    # Seed templates if none exist
    if db.query(InterpretationTemplate).count() == 0:
        seed_templates(db)
    
    db.close()

def seed_planet_interpretations(db):
    """Add basic planet-sign interpretations to database"""
    from app.models import PlanetInterpretation
    
    # Sample data for Sun in each sign
    sun_interpretations = [
        PlanetInterpretation(
            planet="Sun", 
            sign="Aries", 
            interpretation="The Sun in Aries indicates a bold, pioneering spirit. You have a strong drive for independence and are naturally competitive. Leadership comes easily to you, though impatience can be a challenge."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Taurus", 
            interpretation="The Sun in Taurus gives you a patient, determined nature. You value stability and have a strong connection to the material world. You appreciate beauty and comfort, and can be quite stubborn once your mind is made up."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Gemini", 
            interpretation="The Sun in Gemini bestows a curious, versatile mind. You're communicative, quick-witted, and intellectually adaptable. You may have many interests but can sometimes lack follow-through as you chase new ideas."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Cancer", 
            interpretation="The Sun in Cancer creates a sensitive, nurturing personality. You're deeply connected to home and family, with strong protective instincts. Your emotional sensitivity gives you empathy and intuition."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Leo", 
            interpretation="The Sun in Leo brings a warm, creative, and dramatic presence. You naturally draw attention and have leadership abilities. You're generous with others but need recognition and appreciation for your efforts."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Virgo", 
            interpretation="The Sun in Virgo gives an analytical, detail-oriented approach to life. You're practical, discerning, and service-oriented. Your perfectionist tendencies help you excel in your work but can lead to self-criticism."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Libra", 
            interpretation="The Sun in Libra indicates a diplomatic, harmony-seeking nature. You value relationships and fairness, with a natural sense of balance. You may struggle with indecision as you can see all sides of an issue."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Scorpio", 
            interpretation="The Sun in Scorpio creates an intense, passionate personality. You have emotional depth and transformative power, with strong investigative abilities. Trust doesn't come easily, but your loyalty is unwavering once earned."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Sagittarius", 
            interpretation="The Sun in Sagittarius gives an optimistic, freedom-loving spirit. You're philosophical, adventurous, and always seeking to expand your horizons. Honesty is important to you, sometimes to the point of bluntness."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Capricorn", 
            interpretation="The Sun in Capricorn bestows ambition, discipline, and a strong sense of responsibility. You have natural administrative abilities and patience for long-term achievements. Status and recognition motivate you."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Aquarius", 
            interpretation="The Sun in Aquarius creates an independent, progressive thinker. You're humanitarian in outlook and value intellectual freedom. Though socially oriented, you maintain emotional detachment and march to your own drummer."
        ),
        PlanetInterpretation(
            planet="Sun", 
            sign="Pisces", 
            interpretation="The Sun in Pisces indicates a compassionate, imaginative nature. You're highly sensitive to environments and people, with strong creative and intuitive abilities. Boundaries can be challenging as you tend to absorb others' energies."
        ),
    ]
    
    db.add_all(sun_interpretations)
    db.commit()

def seed_house_interpretations(db):
    """Add basic planet-house interpretations to database"""
    from app.models import HouseInterpretation
    
    # Sample data for Sun in each house
    sun_house_interpretations = [
        HouseInterpretation(
            planet="Sun", 
            house=1, 
            interpretation="The Sun in the 1st house gives you a strong, vital personality and natural leadership abilities. Your identity and self-expression are central themes in your life. You have a strong need to express yourself and be recognized."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=2, 
            interpretation="The Sun in the 2nd house puts focus on building security and material resources. Your sense of self-worth is tied to what you possess and create. You have natural abilities in managing resources and developing your talents."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=3, 
            interpretation="The Sun in the 3rd house creates a focus on communication and learning. You shine through your ideas, words, and intellectual pursuits. Your siblings, neighbors, or early education may have played a significant role in shaping your identity."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=4, 
            interpretation="The Sun in the 4th house emphasizes home, family, and emotional foundations. Your private life is where you truly express yourself. Family heritage or your relationship with parents, especially your father, strongly influences your sense of self."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=5, 
            interpretation="The Sun in the 5th house illuminates creativity, pleasure, and self-expression. You shine through creative pursuits, romance, or interactions with children. Risk-taking and playfulness are central to your identity."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=6, 
            interpretation="The Sun in the 6th house focuses your energy on work, service, and health. Your identity is tied to being useful and productive. You may find fulfillment through improving routines, helping others, and developing practical skills."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=7, 
            interpretation="The Sun in the 7th house places emphasis on partnerships and relationships. You find self-expression through collaboration and may learn about yourself through others. Harmony and balance in relationships are essential to your wellbeing."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=8, 
            interpretation="The Sun in the 8th house creates a focus on transformation and shared resources. You may experience repeated personal reinventions throughout life. Issues of power, intimacy, and the taboo fascinate you."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=9, 
            interpretation="The Sun in the 9th house illuminates higher education, philosophy, and exploration. Your identity is tied to expanding your horizons and seeking truth. Travel, formal education, or spiritual pursuits may be central to your personal development."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=10, 
            interpretation="The Sun in the 10th house emphasizes career, public image, and achievements. You're driven to make your mark on the world and may receive public recognition. Authority figures, especially your father, may strongly influence your life path."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=11, 
            interpretation="The Sun in the 11th house focuses energy on groups, friendships, and ideals. You shine through your social connections and contribution to collective causes. Personal goals are often aligned with humanitarian ideals or technological innovation."
        ),
        HouseInterpretation(
            planet="Sun", 
            house=12, 
            interpretation="The Sun in the 12th house creates a focus on the unconscious, compassion, and spiritual service. Your identity may feel somewhat hidden, even from yourself. You may work behind the scenes or in institutions, with a strong connection to collective suffering and healing."
        ),
    ]
    
    db.add_all(sun_house_interpretations)
    db.commit()

def seed_aspect_interpretations(db):
    """Add basic aspect interpretations to database"""
    from app.models import AspectInterpretation
    
    # Sample data for major aspects between Sun and Moon
    sun_moon_aspects = [
        AspectInterpretation(
            planet1="Sun", 
            planet2="Moon", 
            aspect_type="conjunction", 
            interpretation="The Sun conjunct Moon represents a powerful alignment of your conscious will and emotional nature. You experience a strong sense of purpose that aligns with your feelings, giving you emotional clarity about your path. This aspect creates a focused personality with strong vitality."
        ),
        AspectInterpretation(
            planet1="Sun", 
            planet2="Moon", 
            aspect_type="sextile", 
            interpretation="The Sun sextile Moon indicates a harmonious relationship between your will and emotions. Your conscious goals work easily with your instinctive reactions, allowing you to balance action with reflection. This creates opportunities for emotional satisfaction through purposeful activity."
        ),
        AspectInterpretation(
            planet1="Sun", 
            planet2="Moon", 
            aspect_type="square", 
            interpretation="The Sun square Moon creates a dynamic tension between your conscious purpose and emotional needs. You may experience internal conflict between what you think you should do and what you feel. This aspect generates creative energy but requires integration of these opposing forces."
        ),
        AspectInterpretation(
            planet1="Sun", 
            planet2="Moon", 
            aspect_type="trine", 
            interpretation="The Sun trine Moon provides a natural flow between your will and emotions. Your conscious identity and subconscious feelings support each other, giving you emotional resilience and a harmonious personality. You find it easy to express your authentic self."
        ),
        AspectInterpretation(
            planet1="Sun", 
            planet2="Moon", 
            aspect_type="opposition", 
            interpretation="The Sun opposition Moon indicates a polarization between your conscious objectives and emotional needs. You may feel pulled in opposite directions or project one aspect of yourself onto others. This aspect brings relationship themes into focus and requires balance."
        ),
    ]
    
    db.add_all(sun_moon_aspects)
    db.commit()

def seed_api_keys(db):
    """Add default API keys to database"""
    from app.models import ApiKey
    
    # Create a default API key for testing
    default_keys = [
        ApiKey(
            key="Michael",
            name="Default API Key",
            enabled=True,
            rate_limit=1000  # Higher limit for default key
        ),
        ApiKey(
            key="test_key_1234567890",
            name="Test API Key",
            enabled=True,
            rate_limit=100
        )
    ]
    
    db.add_all(default_keys)
    db.commit()

def seed_templates(db):
    """Add basic interpretation templates to database"""
    from app.models import InterpretationTemplate
    
    templates = [
        InterpretationTemplate(
            name="basic_text",
            format_type="text",
            template_content="""
# Natal Chart Interpretation for {{birth_date}}

## Planetary Positions
{% for planet in planets %}
{{ planet.name }} in {{ planet.sign }} ({{ planet.degree }}° {{ planet.minutes }}') in House {{ planet.house }}
{% if planet.retrograde %}Retrograde{% endif %}

{% endfor %}

## House Cusps
{% for house in houses %}
House {{ house.number }}: {{ house.sign }} ({{ house.degree }}° {{ house.minutes }}')
{% endfor %}

## Major Aspects
{% for aspect in aspects %}
{{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }} (Orb: {{ aspect.orb }}°)
{% endfor %}

## Chart Angles
Ascendant: {{ angles.ascendant.sign }} ({{ angles.ascendant.degree }}° {{ angles.ascendant.minutes }}')
Midheaven: {{ angles.midheaven.sign }} ({{ angles.midheaven.degree }}° {{ angles.midheaven.minutes }}')
Descendant: {{ angles.descendant.sign }} ({{ angles.descendant.degree }}° {{ angles.descendant.minutes }}')
Imum Coeli: {{ angles.imum_coeli.sign }} ({{ angles.imum_coeli.degree }}° {{ angles.imum_coeli.minutes }}')
"""
        ),
        InterpretationTemplate(
            name="detailed_html",
            format_type="html",
            template_content="""
<!DOCTYPE html>
<html>
<head>
    <title>Natal Chart Interpretation</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #4a4a4a; }
        h2 { color: #7e57c2; margin-top: 30px; }
        h3 { color: #5c6bc0; }
        .planet { margin-bottom: 20px; }
        .aspect { margin-bottom: 10px; }
        .house { margin-bottom: 10px; }
        .retrograde { color: #e53935; }
        .interpretation { background-color: #f5f5f5; padding: 10px; border-left: 3px solid #7e57c2; }
    </style>
</head>
<body>
    <h1>Natal Chart Interpretation</h1>
    <p><strong>Birth Data:</strong> {{birth_date}} at {{birth_time}}, {{timezone}}</p>
    <p><strong>Location:</strong> Latitude {{latitude}}, Longitude {{longitude}}</p>
    
    <h2>Planetary Positions</h2>
    {% for planet in planets %}
    <div class="planet">
        <h3>{{ planet.name }} in {{ planet.sign }} ({{ planet.degree }}° {{ planet.minutes }}') in House {{ planet.house }}
        {% if planet.retrograde %}<span class="retrograde">Retrograde</span>{% endif %}</h3>
        <div class="interpretation">
            <p>{{ planet_interpretations[planet.name][planet.sign] }}</p>
            <p>{{ house_interpretations[planet.name][planet.house] }}</p>
        </div>
    </div>
    {% endfor %}
    
    <h2>Major Aspects</h2>
    {% for aspect in aspects %}
    <div class="aspect">
        <h3>{{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }} (Orb: {{ aspect.orb }}°)</h3>
        <div class="interpretation">
            <p>{{ aspect_interpretations[aspect.planet1][aspect.planet2][aspect.aspect_type] }}</p>
        </div>
    </div>
    {% endfor %}
    
    <h2>Chart Angles</h2>
    <div class="house">
        <p><strong>Ascendant:</strong> {{ angles.ascendant.sign }} ({{ angles.ascendant.degree }}° {{ angles.ascendant.minutes }}')</p>
        <p><strong>Midheaven:</strong> {{ angles.midheaven.sign }} ({{ angles.midheaven.degree }}° {{ angles.midheaven.minutes }}')</p>
        <p><strong>Descendant:</strong> {{ angles.descendant.sign }} ({{ angles.descendant.degree }}° {{ angles.descendant.minutes }}')</p>
        <p><strong>Imum Coeli:</strong> {{ angles.imum_coeli.sign }} ({{ angles.imum_coeli.degree }}° {{ angles.imum_coeli.minutes }}')</p>
    </div>
</body>
</html>
"""
        ),
        InterpretationTemplate(
            name="markdown_template",
            format_type="markdown",
            template_content="""
# Natal Chart Interpretation

**Birth Data:** {{birth_date}} at {{birth_time}}, {{timezone}}  
**Location:** Latitude {{latitude}}, Longitude {{longitude}}

## Planetary Positions

{% for planet in planets %}
### {{ planet.name }} in {{ planet.sign }} ({{ planet.degree }}° {{ planet.minutes }}') in House {{ planet.house }} {% if planet.retrograde %}*Retrograde*{% endif %}

{{ planet_interpretations[planet.name][planet.sign] }}

{{ house_interpretations[planet.name][planet.house] }}

{% endfor %}

## Major Aspects

{% for aspect in aspects %}
### {{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }} (Orb: {{ aspect.orb }}°)

{{ aspect_interpretations[aspect.planet1][aspect.planet2][aspect.aspect_type] }}

{% endfor %}

## Chart Angles

**Ascendant:** {{ angles.ascendant.sign }} ({{ angles.ascendant.degree }}° {{ angles.ascendant.minutes }}')  
**Midheaven:** {{ angles.midheaven.sign }} ({{ angles.midheaven.degree }}° {{ angles.midheaven.minutes }}')  
**Descendant:** {{ angles.descendant.sign }} ({{ angles.descendant.degree }}° {{ angles.descendant.minutes }}')  
**Imum Coeli:** {{ angles.imum_coeli.sign }} ({{ angles.imum_coeli.degree }}° {{ angles.imum_coeli.minutes }}')
"""
        )
    ]
    
    db.add_all(templates)
    db.commit()
