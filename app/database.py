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

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,             # Check connection before use
    pool_recycle=300,               # Recycle connections after 5 minutes
    pool_size=5,                    # Set a reasonable pool size 
    max_overflow=10,                # Allow some overflow connections
    connect_args={"sslmode": "require"}  # Ensure SSL connections
)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """
    Get a database session
    Used as a dependency in FastAPI endpoints
    
    Returns:
        SQLAlchemy database session that will be closed after usage
        
    Raises:
        HTTPException: If database connection fails
    """
    db = None
    try:
        db = SessionLocal()
        # Execute a simple query to test the connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        yield db
    except Exception as e:
        # Log the database connection error
        import logging
        logging.error(f"Database connection error: {str(e)}")
        
        # Raise HTTP exception for the client
        from fastapi import HTTPException
        from fastapi import status
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later."
        )
    finally:
        if db:
            db.close()

def init_db():
    """Initialize the database with tables and seed data"""
    from app.models import Base, PlanetInterpretation, HouseInterpretation, AspectInterpretation, InterpretationTemplate, ApiKey, UserProfile
    
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
    
    # Seed admin user profile
    seed_user_profiles(db)
    
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
    
    # Sample data for Moon in each sign
    moon_interpretations = [
        PlanetInterpretation(
            planet="Moon", 
            sign="Aries", 
            interpretation="The Moon in Aries gives quick emotional reactions and a need for independence in your emotional life. You process feelings through action and prefer direct expression. You may be impulsive in emotional matters but quick to move on from upsets."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Taurus", 
            interpretation="The Moon in Taurus creates a need for emotional security and stability. You process feelings slowly and thoroughly, preferring predictable emotional environments. Physical comfort, good food, and beautiful surroundings help you feel emotionally secure."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Gemini", 
            interpretation="The Moon in Gemini gives an intellectually responsive emotional nature. You process feelings through talking and analyzing, needing mental stimulation for emotional satisfaction. Your moods can change quickly, and you're adaptable in emotional matters."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Cancer", 
            interpretation="The Moon in Cancer creates deep emotional sensitivity and strong nurturing instincts. This is the Moon's home sign, making your emotional nature particularly powerful. You're protective of loved ones and deeply connected to family and home."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Leo", 
            interpretation="The Moon in Leo gives warm, generous emotional expressions and a need for approval. You process feelings through creative outlets and dramatic expression. You take pride in your emotional strength and loyalty to those you love."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Virgo", 
            interpretation="The Moon in Virgo creates an analytical approach to emotions and a need for order in your emotional life. You process feelings by organizing, categorizing, and problem-solving. You may be self-critical but excel at practical emotional support for others."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Libra", 
            interpretation="The Moon in Libra gives a harmonious emotional nature and a need for balanced relationships. You process feelings through connection with others and seek emotional equilibrium. Peace and beauty in your environment are essential for your emotional wellbeing."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Scorpio", 
            interpretation="The Moon in Scorpio creates intense emotional depth and a powerful intuitive sense. You process feelings through transformation and deep psychological understanding. You form profound emotional bonds and may be guarded until trust is established."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Sagittarius", 
            interpretation="The Moon in Sagittarius gives an optimistic emotional outlook and a need for emotional freedom. You process feelings through philosophy and broader meaning. Emotional exploration and adventure help you feel secure and fulfilled."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Capricorn", 
            interpretation="The Moon in Capricorn creates emotional restraint and a need for achievement to feel secure. You process feelings through practical action and responsibility. You may appear reserved emotionally but have deep, enduring attachments."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Aquarius", 
            interpretation="The Moon in Aquarius gives an unconventional emotional nature and a need for intellectual freedom. You process feelings through unique perspectives and humanitarian ideals. You value emotional independence and may detach when feelings become overwhelming."
        ),
        PlanetInterpretation(
            planet="Moon", 
            sign="Pisces", 
            interpretation="The Moon in Pisces creates a highly empathic, compassionate emotional nature. You process feelings through intuitive understanding and creative or spiritual outlets. Boundaries with others' emotions can be challenging as you naturally absorb surrounding energies."
        ),
    ]
    
    # Add all interpretations to the database
    db.add_all(sun_interpretations)
    db.add_all(moon_interpretations)
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
            interpretation="The Sun opposite Moon creates a clear polarity between your conscious will and emotional responses. You may feel pulled between your rational goals and emotional needs, leading to relationship patterns that mirror this internal dynamic. Integration of these opposites brings powerful self-awareness."
        ),
    ]
    
    db.add_all(sun_moon_aspects)
    db.commit()

def seed_templates(db):
    """Add basic interpretation templates to database"""
    from app.models import InterpretationTemplate
    
    # Basic text template
    basic_text = InterpretationTemplate(
        name="basic_text",
        format_type="text",
        template_content="""# Natal Chart Interpretation

**Birth Information:**
- Date: {{ birth_info.birth_date }}
- Time: {{ birth_info.birth_time }}
- Coordinates: {{ birth_info.latitude }}° {{ 'N' if birth_info.latitude >= 0 else 'S' }}, {{ birth_info.longitude }}° {{ 'E' if birth_info.longitude >= 0 else 'W' }}
- Timezone: {{ birth_info.timezone }}

## Sun in {{ sun.sign }}
{{ sun_sign_interpretation }}

## Moon in {{ moon.sign }}
{{ moon_sign_interpretation }}

## Ascendant in {{ ascendant.sign }}
The Ascendant represents your outward personality and how others perceive you. With {{ ascendant.sign }} rising, you come across as {{ ascendant_keywords }}.

## Planetary Positions
{% for planet in planets %}
- {{ planet.name }} in {{ planet.sign }} ({{ planet.house }}{{ 'st' if planet.house == 1 else 'nd' if planet.house == 2 else 'rd' if planet.house == 3 else 'th' }} house)
{% endfor %}

## Major Aspects
{% for aspect in major_aspects %}
- {{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }} (orb: {{ aspect.orb|round(1) }}°)
{% endfor %}
"""
    )
    
    # Markdown template
    markdown = InterpretationTemplate(
        name="markdown",
        format_type="markdown",
        template_content="""# Natal Chart Interpretation

**Birth Information:**
- Date: {{ birth_info.birth_date }}
- Time: {{ birth_info.birth_time }}
- Coordinates: {{ birth_info.latitude }}° {{ 'N' if birth_info.latitude >= 0 else 'S' }}, {{ birth_info.longitude }}° {{ 'E' if birth_info.longitude >= 0 else 'W' }}
- Timezone: {{ birth_info.timezone }}

## Sun in {{ sun.sign }}
{{ sun_sign_interpretation }}

## Moon in {{ moon.sign }}
{{ moon_sign_interpretation }}

## Ascendant in {{ ascendant.sign }}
The Ascendant represents your outward personality and how others perceive you. With {{ ascendant.sign }} rising, you come across as {{ ascendant_keywords }}.

## Planetary Positions
{% for planet in planets %}
- **{{ planet.name }}** in **{{ planet.sign }}** ({{ planet.house }}{{ 'st' if planet.house == 1 else 'nd' if planet.house == 2 else 'rd' if planet.house == 3 else 'th' }} house)
{% endfor %}

## Major Aspects
{% for aspect in major_aspects %}
- **{{ aspect.planet1 }}** {{ aspect.aspect_type }} **{{ aspect.planet2 }}** (orb: {{ aspect.orb|round(1) }}°)
{% endfor %}
"""
    )
    
    # Concise template - more compact with just essential information
    concise = InterpretationTemplate(
        name="concise",
        format_type="text",
        template_content="""# Natal Chart Summary 
**Birth:** {{ birth_info.birth_date }} {{ birth_info.birth_time }} ({{ birth_info.timezone }})

## Key Placements
- Sun: {{ sun.sign }} ({{ sun.house }}H)
- Moon: {{ moon.sign }} ({{ moon.house }}H)
- Ascendant: {{ ascendant.sign }}

## Major Aspects
{% for aspect in major_aspects %}
- {{ aspect.planet1 }} {{ aspect.aspect_type }} {{ aspect.planet2 }}
{% endfor %}

## Elements & Modalities
Fire: {% set fire_count = planets|selectattr('sign', 'in', ['Aries', 'Leo', 'Sagittarius'])|list|length %}
Earth: {% set earth_count = planets|selectattr('sign', 'in', ['Taurus', 'Virgo', 'Capricorn'])|list|length %}
Air: {% set air_count = planets|selectattr('sign', 'in', ['Gemini', 'Libra', 'Aquarius'])|list|length %}
Water: {% set water_count = planets|selectattr('sign', 'in', ['Cancer', 'Scorpio', 'Pisces'])|list|length %}

Cardinal: {% set cardinal_count = planets|selectattr('sign', 'in', ['Aries', 'Cancer', 'Libra', 'Capricorn'])|list|length %}
Fixed: {% set fixed_count = planets|selectattr('sign', 'in', ['Taurus', 'Leo', 'Scorpio', 'Aquarius'])|list|length %}
Mutable: {% set mutable_count = planets|selectattr('sign', 'in', ['Gemini', 'Virgo', 'Sagittarius', 'Pisces'])|list|length %}

Fire: {{ fire_count }} | Earth: {{ earth_count }} | Air: {{ air_count }} | Water: {{ water_count }}
Cardinal: {{ cardinal_count }} | Fixed: {{ fixed_count }} | Mutable: {{ mutable_count }}
"""
    )
    
    # Detailed Markdown template
    detailed_markdown = InterpretationTemplate(
        name="detailed_markdown",
        format_type="markdown",
        template_content="""# Comprehensive Natal Chart Interpretation

**Birth Details:**
- **Date:** {{ birth_info.birth_date }}
- **Time:** {{ birth_info.birth_time }}
- **Location:** {{ birth_info.latitude }}° {{ 'N' if birth_info.latitude >= 0 else 'S' }}, {{ birth_info.longitude }}° {{ 'E' if birth_info.longitude >= 0 else 'W' }}
- **Timezone:** {{ birth_info.timezone }}

## Core Planetary Placements

### ☉ Sun in {{ sun.sign }} ({{ sun.house }}{{ 'st' if sun.house == 1 else 'nd' if sun.house == 2 else 'rd' if sun.house == 3 else 'th' }} House)
{{ sun_sign_interpretation }}

### ☽ Moon in {{ moon.sign }} ({{ moon.house }}{{ 'st' if moon.house == 1 else 'nd' if moon.house == 2 else 'rd' if moon.house == 3 else 'th' }} House)
{{ moon_sign_interpretation }}

### ↑ Ascendant in {{ ascendant.sign }}
The Ascendant represents your outward personality and how others perceive you. With {{ ascendant.sign }} rising, you come across as {{ ascendant_keywords }}.

## All Planetary Positions
{% for planet in planets %}
- **{{ planet.name }}** in **{{ planet.sign }}** ({{ planet.house }}{{ 'st' if planet.house == 1 else 'nd' if planet.house == 2 else 'rd' if planet.house == 3 else 'th' }} house){% if planet.retrograde %} *Retrograde*{% endif %}
{% endfor %}

## Major Aspects & Patterns
{% for aspect in major_aspects %}
- **{{ aspect.planet1 }}** {{ aspect.aspect_type }} **{{ aspect.planet2 }}** (orb: {{ aspect.orb|round(1) }}°)
{% endfor %}

## House Cusps
{% for house in houses %}
- House {{ house.number }}: {{ house.sign }} {{ house.degree }}°{{ house.minutes }}'
{% endfor %}
"""
    )
    
    db.add_all([basic_text, markdown, concise, detailed_markdown])
    db.commit()

def seed_user_profiles(db):
    """Add admin user profile to database if it doesn't exist"""
    from app.models import UserProfile
    import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if Parker Todd's profile exists
    profile = db.query(UserProfile).filter(UserProfile.name == "Parker Todd").first()
    if not profile:
        # Create Parker Todd's profile with admin privileges
        admin_profile = UserProfile(
            name="Parker Todd",
            birth_date="2000-04-11",  # April 11, 2000
            birth_time="16:30",
            latitude=43.615,          # Boise, ID latitude
            longitude=-116.2023,      # Boise, ID longitude
            timezone="America/Boise",
            notes="Creator and Admin of Natal Astrology Engine",
            is_admin=True,
            created_at=datetime.datetime.now().isoformat()
        )
        db.add(admin_profile)
        db.commit()
        logger.info("Created admin profile for Parker Todd")
    else:
        # Update the birth date if it's not correct
        if profile.birth_date != "2000-04-11":
            profile.birth_date = "2000-04-11"  # April 11, 2000
            db.commit()
            logger.info("Updated Parker Todd's birth date to April 11, 2000")
        else:
            logger.info("Admin profile for Parker Todd already exists")


def seed_api_keys(db):
    """Add default API keys to database if they don't exist"""
    from app.models import ApiKey
    import secrets
    from datetime import datetime
    import logging
    
    logger = logging.getLogger(__name__)
    
    # Check if test key already exists
    test_key_value = "test_key_1234567890"
    existing_test_key = db.query(ApiKey).filter(ApiKey.key == test_key_value).first()
    
    # Check if we have a default key already
    existing_default_key = db.query(ApiKey).filter(ApiKey.name == "Default API Key").first()
    
    new_keys = []
    
    # Create a fixed test API key for development if it doesn't exist
    if not existing_test_key:
        test_key = ApiKey(
            key=test_key_value,
            name="Test API Key",
            enabled=True,
            rate_limit=100,  # Requests per minute
            daily_limit=1000,  # Requests per day
            created_at=datetime.now().isoformat()
        )
        new_keys.append(test_key)
        logger.info("Created test API key")
    else:
        logger.info("Test API key already exists")
    
    # Create a default API key if none exists
    if not existing_default_key:
        default_key = ApiKey(
            key=secrets.token_hex(32),
            name="Default API Key",
            enabled=True,
            rate_limit=60,  # Requests per minute
            daily_limit=1000,  # Requests per day
            created_at=datetime.now().isoformat()
        )
        new_keys.append(default_key)
        logger.info("Created default API key")
    else:
        logger.info("Default API key already exists")
    
    # If we have new keys, add them
    if new_keys:
        db.add_all(new_keys)
        db.commit()
        
        # Log the keys that were created
        for key in new_keys:
            logger.info(f"API key created: {key.name} ({key.key})")
    
    # Always create a new secure key for this session
    secure_key = ApiKey(
        key=secrets.token_hex(32),
        name="Production API Key",
        enabled=True,
        rate_limit=60,  # Requests per minute
        daily_limit=1000,  # Requests per day
        created_at=datetime.now().isoformat()
    )
    db.add(secure_key)
    db.commit()
    
    logger.info(f"Created new production API key: {secure_key.key}")
    
    # Print all available keys for reference
    all_keys = db.query(ApiKey).all()
    logger.info(f"Available API keys:")
    for key in all_keys:
        logger.info(f"- {key.name}: {key.key} (enabled: {key.enabled})")
