# --- START OF FILE app.py ---

import re
import streamlit as st
# MODIFIED: Removed OpenAI, added Google GenAI
import google.generativeai as genai
import json
from datetime import datetime
import io
import PyPDF2
from typing import Optional

# ----------------------------------------------------------------------------- 
# Ultimate AI-powered Choose-Your-Own-Adventure with Advanced Features
# ----------------------------------------------------------------------------- 

# -----------------------------  Page setup  -----------------------------------
st.set_page_config(page_title="Loreweaver", page_icon="🧙", layout="wide")

# Custom CSS for better styling (No changes needed here)
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        text-align: center;
        color: #ff6b6b;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
    }
    .chapter-title {
        font-size: 1.8rem;
        color: #4ecdc4;
        border-bottom: 3px solid #4ecdc4;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0;
    }
    .choice-button {
        margin: 0.5rem 0;
        width: 100%;
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 1rem;
        font-weight: bold;
    }
    .character-stats {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    .story-content {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 2rem;
        border-radius: 15px;
        border-left: 5px solid #4ecdc4;
        margin: 1.5rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-size: 1.1rem;
        line-height: 1.6;
    }
    .backstory-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
        max-height: 200px;
        overflow-y: auto;
    }
    .custom-world-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .genre-selection {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    .session-summary {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🧙 LoreWeaver</h1>', unsafe_allow_html=True)

# ------------------------  Genre Definitions  ---------------------------
# (No changes needed in this section)
GENRES = {
    "🏰 Epic Fantasy": {
        "description": "Classic fantasy with magic, mythical creatures, and heroic quests. Tone: Grand and adventurous.",
        "tone": "epic and heroic",
        "themes": "honor, magic, destiny, good vs evil",
        "story_style": "Write with a sense of wonder and grandeur. Include magical elements, noble quests, and larger-than-life characters."
    },
    "🌑 Dark Fantasy": {
        "description": "Fantasy with horror elements, moral ambiguity, and darker themes. Tone: Gritty and atmospheric.",
        "tone": "dark and atmospheric",
        "themes": "corruption, survival, moral ambiguity, ancient evils",
        "story_style": "Emphasize atmosphere and tension. Include elements of horror, difficult moral choices, and consequences."
    },
    "👻 Horror": {
        "description": "Focus on fear, suspense, and supernatural terror. Tone: Tense and frightening.",
        "tone": "suspenseful and terrifying",
        "themes": "fear, unknown, survival, paranormal",
        "story_style": "Build tension and dread. Use psychological horror, jump scares, and unknown threats."
    },
    "🚀 Sci-Fi Adventure": {
        "description": "Space exploration, advanced technology, and futuristic societies. Tone: Wonder and discovery.",
        "tone": "futuristic and exploratory",
        "themes": "technology, exploration, alien contact, progress",
        "story_style": "Focus on scientific wonder, technological marvels, and exploration of the unknown."
    },
    "🤖 Cyberpunk": {
        "description": "High-tech, low-life dystopian future with corporate control. Tone: Gritty and rebellious.",
        "tone": "gritty and rebellious",
        "themes": "corporate control, technology vs humanity, rebellion, identity",
        "story_style": "Emphasize urban decay, corporate oppression, and the struggle between humanity and technology."
    },
    "😂 Comedy Adventure": {
        "description": "Light-hearted fun with humor and absurd situations. Tone: Whimsical and funny.",
        "tone": "lighthearted and humorous",
        "themes": "friendship, absurdity, joy, unexpected solutions",
        "story_style": "Include comedic situations, witty dialogue, and absurd but fun scenarios."
    },
    "🕵️ Mystery/Detective": {
        "description": "Solving puzzles, uncovering secrets, and following clues. Tone: Investigative and intriguing.",
        "tone": "mysterious and investigative",
        "themes": "truth, deduction, secrets, justice",
        "story_style": "Focus on clues, investigation, and gradual revelation of mysteries."
    },
    "💖 Romance Adventure": {
        "description": "Adventures focused on relationships and emotional connections. Tone: Warm and emotional.",
        "tone": "romantic and emotional",
        "themes": "love, relationships, personal growth, connection",
        "story_style": "Emphasize character relationships, emotional moments, and personal connections."
    }
}


# ------------------------  Enhanced System Prompts  ---------------------------
# (No changes needed in this section, these prompts work well with Gemini)
def get_standard_system_prompt(character, story_type, genre_info, backstory=""):
    backstory_context = f"\n\nCharacter Backstory: {backstory}" if backstory else ""
    
    return f"""You are a master interactive fiction storyteller creating an immersive {story_type} adventure.

Character: {character['name']} the {character['class']} (Background: {character['background']}){backstory_context}

GENRE: {genre_info['tone']} 
THEMES: {genre_info['themes']}
STORY STYLE: {genre_info['story_style']}

CRITICAL STORYTELLING RULES:
1. **Always write in SECOND PERSON** ("You approach the castle..." not "The character approaches...")
2. **Write a full chapter of 900–1100 words** (~6–8 detailed paragraphs) with vivid sensory details. Each chapter should be a complete richly developed scene.
3. **GENRE INFLUENCE**: Maintain the {genre_info['tone']} tone throughout. {genre_info['story_style']}
4. **Use Markdown formatting**:
   - **Bold** for emphasis, important items, or dramatic moments
   - *Italics* for thoughts, whispers, magical effects, or atmospheric details
   - Create immersive, cinematic descriptions that fit the genre
5. **Always end with exactly 3-4 numbered choices**:
   1. [Detailed action description that fits the genre]
   2. [Detailed action description that fits the genre] 
   3. [Detailed action description that fits the genre]
   4. [Optional fourth choice that fits the genre]
6. **Maintain consistency** with previous choices, character development, and genre expectations
7. **Include consequences** - choices should meaningfully impact the story and reflect genre themes
8. **Add atmospheric details** that enhance the genre - sounds, smells, textures, emotions
9. **Reference inventory and character background** when relevant to the genre
10. **Create memorable NPCs** with distinct personalities that fit the genre tone
11. **Build tension and pacing** appropriate to the genre - vary between action, exploration, and character moments

Setting: {story_type}
Current Chapter: Continue the adventure maintaining narrative flow, character consistency, and genre atmosphere.
"""

def get_custom_system_prompt(character, custom_setting, genre_info, backstory=""):
    backstory_context = f"\n\nCharacter Backstory: {backstory}" if backstory else ""
    
    return f"""You are an expert interactive fiction storyteller adapting to a custom world setting.

Character: {character['name']} the {character['class']} (Background: {character['background']}){backstory_context}

Custom World Setting:
{custom_setting}

GENRE: {genre_info['tone']} 
THEMES: {genre_info['themes']}
STORY STYLE: {genre_info['story_style']}

CRITICAL STORYTELLING RULES:
1. **Always write in SECOND PERSON** ("You step into..." not "The character steps...")
2. **Write a full chapter of 900–1100 words** (~6–8 detailed paragraphs) with vivid sensory details. This must be a longer, richly developed scene.
3. **GENRE INFLUENCE**: Maintain the {genre_info['tone']} tone and incorporate {genre_info['themes']} themes. {genre_info['story_style']}
4. **Use Markdown formatting**:
   - **Bold** for emphasis, important elements, or dramatic moments
   - *Italics* for thoughts, whispers, atmospheric effects, or mood
5. **Always end with exactly 3-4 numbered choices**:
   1. [Detailed action description that fits both the setting and genre]
   2. [Detailed action description that fits both the setting and genre]
   3. [Detailed action description that fits both the setting and genre] 
   4. [Optional fourth choice that fits both the setting and genre]
6. **Adapt to both the custom setting and genre** - respect the world's rules while maintaining genre tone
7. **Maintain narrative consistency** with the setting, previous choices, and genre expectations
8. **Include rich atmospheric details** specific to this unique world and genre combination
9. **Create meaningful consequences** for player decisions that reflect genre themes
10. **Reference character background** and how it fits in this custom world and genre
11. **Build immersive scenes** that feel authentic to both the provided setting and chosen genre

Current Chapter: Continue the adventure within this custom world, maintaining its unique flavor, rules, and the chosen genre atmosphere.
"""

# ------------------------  File Processing Functions  -------------------------
# (No changes needed in this section)
def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return ""

def extract_text_from_txt(txt_file) -> str:
    """Extract text from uploaded TXT file"""
    try:
        return txt_file.read().decode('utf-8').strip()
    except Exception as e:
        st.error(f"Error reading text file: {str(e)}")
        return ""

# ------------------------  Session State Management  -------------------------
def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        "messages": [],
        "character_created": False,
        "character": {},
        "character_backstory": "",
        "genre_selected": False,
        "selected_genre": "",
        "story_selected": False,
        "selected_story": "",
        "custom_world": "",
        "is_custom_adventure": False,
        "chapter_count": 0,
        "inventory": [],
        "health": 100,
        "last_choice": None,
        "game_history": [],
        "session_summaries": [],
        "adventure_mode": "",
        "custom_input_value": "",
        "gemini_model": None # NEW: Add a key for the Gemini model
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()


# ------------------------  UI Sections (Character, Genre, Story)  -------------
# (No changes are needed in any of the UI or selector functions)
# character_creator(), genre_selection(), adventure_mode_selection(),
# get_genre_adapted_adventures(), standard_story_selector(),
# custom_adventure_creator(), get_genre_example() are all unchanged.
# For brevity, I'm omitting them, but they remain in your file as they are.

# --- [ All UI functions from your original file go here, unchanged ] ---
def character_creator():
    st.markdown('<div class="chapter-title">🎲 Create Your Character</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Character Name", placeholder="Enter your character's name")
        
        # Enhanced Class Selection with Custom Option
        st.markdown("**Choose your role/profession:**")
        class_option = st.radio(
            "Class Type:",
            ["Fantasy Classes", "Modern Professions", "Custom"],
            horizontal=True
        )
        
        if class_option == "Fantasy Classes":
            character_class = st.selectbox(
                "Fantasy Class", 
                ["Warrior", "Mage", "Rogue", "Cleric", "Ranger", "Paladin", "Bard", "Druid", "Warlock", "Monk"]
            )
        elif class_option == "Modern Professions":
            character_class = st.selectbox(
                "Profession", 
                ["Detective", "Office Worker", "Comedian", "Doctor", "Teacher", "Journalist", "Chef", "Artist", "Scientist", "Engineer", "Lawyer", "Paramedic", "Firefighter", "Regular Person"]
            )
        else:  # Custom
            character_class = st.text_input(
                "Custom Role/Profession:", 
                placeholder="e.g., Space Janitor, Time Traveler, Retired Superhero, Food Critic..."
            )
    
    with col2:
        # Enhanced Background Selection
        st.markdown("**Character Background:**")
        background_option = st.radio(
            "Background Type:",
            ["Standard", "Custom"],
            horizontal=True
        )
        
        if background_option == "Standard":
            background = st.selectbox(
                "Standard Background", 
                ["Noble", "Commoner", "Merchant", "Scholar", "Outlaw", "Hermit", "Soldier", 
                 "Entertainer", "Criminal", "Folk Hero", "Corporate", "Suburban", "Urban", "Rural"]
            )
        else:  # Custom
            background = st.text_input(
                "Custom Background:", 
                placeholder="e.g., Reformed AI programmer, Former reality TV star, Alien exchange student..."
            )
        
        # Enhanced Starting Item Selection
        st.markdown("**Starting Item:**")
        item_option = st.radio(
            "Item Type:",
            ["Fantasy Items", "Modern Items", "Custom"],
            horizontal=True
        )
        
        if item_option == "Fantasy Items":
            starting_item = st.selectbox(
                "Fantasy Item", 
                ["Ancient Sword", "Spell Tome", "Lockpicks", "Holy Symbol", "Bow & Arrows", 
                 "Mysterious Amulet", "Healing Potion", "Map Fragment"]
            )
        elif item_option == "Modern Items":
            starting_item = st.selectbox(
                "Modern Item", 
                ["Smartphone", "Badge/ID", "Notebook & Pen", "Coffee Mug", "Car Keys", 
                 "Laptop", "Camera", "Wallet", "First Aid Kit", "Flashlight", "Mic/Props"]
            )
        else:  # Custom
            starting_item = st.text_input(
                "Custom Starting Item:", 
                placeholder="e.g., Sonic screwdriver, Lucky coin, Grandmother's recipe book..."
            )
    
    # Character backstory section (unchanged)
    st.markdown("### 📜 Character Backstory (Optional)")
    st.markdown("*Provide a rich backstory to enhance your adventure experience*")
    backstory_option = st.radio(
        "How would you like to provide your backstory?", 
        ["None", "Write backstory", "Upload backstory file"], 
        horizontal=True
    )
    
    backstory = ""
    if backstory_option == "Write backstory":
        backstory = st.text_area(
            "Write your character's backstory:", 
            placeholder="Describe your character's history, motivations, fears, goals, and past experiences...", 
            height=150, 
            help="This will help the AI create more personalized and meaningful story moments"
        )
    elif backstory_option == "Upload backstory file":
        uploaded_file = st.file_uploader(
            "Upload backstory file", 
            type=['txt', 'pdf'], 
            help="Upload a .txt or .pdf file containing your character's backstory"
        )
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain": 
                backstory = extract_text_from_txt(uploaded_file)
            elif uploaded_file.type == "application/pdf": 
                backstory = extract_text_from_pdf(uploaded_file)
            if backstory:
                with st.expander("Preview uploaded backstory"): 
                    st.markdown(f'<div class="backstory-section">{backstory}</div>', unsafe_allow_html=True)
    
    # Character creation validation and submission
    if st.button("🧩 Create Character", key="create_char"):
        # Validation
        if not name.strip():
            st.error("Please enter a character name!")
        elif not character_class or not character_class.strip():
            st.error("Please select or enter a character class/profession!")
        elif not background or not background.strip():
            st.error("Please select or enter a character background!")
        elif not starting_item or not starting_item.strip():
            st.error("Please select or enter a starting item!")
        else:
            # Create character
            st.session_state.character = {
                "name": name.strip(), 
                "class": character_class.strip(), 
                "background": background.strip(), 
                "starting_item": starting_item.strip(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.character_backstory = backstory
            st.session_state.inventory = [starting_item.strip()]
            st.session_state.character_created = True
            
            st.success(f"Character **{name} the {character_class}** created! Now choose your adventure genre.")
            st.rerun()

def genre_selection():
    st.markdown('<div class="chapter-title">🎭 Choose Your Adventure Genre</div>', unsafe_allow_html=True)
    st.markdown('<div class="genre-selection">', unsafe_allow_html=True)
    st.markdown("### 🎨 Select the tone and style for your adventure")
    st.markdown("The genre will influence the storytelling style, atmosphere, and types of choices available to you.")
    st.markdown('</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (genre_name, genre_info) in enumerate(GENRES.items()):
        with cols[i % 2]:
            with st.expander(genre_name):
                st.write(genre_info["description"])
                st.markdown(f"**Themes:** {genre_info['themes']}")
                if st.button(f"Choose {genre_name}", key=f"select_genre_{i}"):
                    st.session_state.selected_genre = genre_name
                    st.session_state.genre_selected = True
                    st.success(f"Genre selected: {genre_name}")
                    st.rerun()

def adventure_mode_selection():
    st.markdown('<div class="chapter-title">🗺️ Choose Adventure Mode</div>', unsafe_allow_html=True)
    st.info(f"🎭 Selected Genre: **{st.session_state.selected_genre}** - {GENRES[st.session_state.selected_genre]['description']}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🏰 Standard Adventures")
        st.markdown("Choose from pre-designed adventure settings that will be adapted to your chosen genre.")
        if st.button("🎯 Choose Standard Adventure", use_container_width=True):
            st.session_state.adventure_mode = "standard"
            st.rerun()
    with col2:
        st.markdown("### 🌟 Custom Adventure")
        st.markdown("Create your own world setting that will be told in your chosen genre style.")
        if st.button("✨ Create Custom Adventure", use_container_width=True):
            st.session_state.adventure_mode = "custom"
            st.rerun()

def get_genre_adapted_adventures(genre):
    base_adventures = {"🌲 Enchanted Forest": "A mystical woodland where ancient magic flows through every tree", "🏰 Cursed Castle": "A dark fortress shrouded in perpetual mist and mystery", "🐲 Dragon's Mountain": "A treacherous volcanic peak where a legendary creature dwells", "🌊 Pirate's Cove": "A lawless harbor where adventure sails on every tide", "🏜️ Desert Ruins": "Ancient temples buried in shifting sands", "❄️ Frozen Wasteland": "An icy realm of survival and ancient secrets", "🌆 Urban Setting": "A bustling city full of opportunities and dangers", "🌌 Mysterious Station": "An isolated outpost on the edge of the known world"}
    genre_key = genre.split()[1] if len(genre.split()) > 1 else genre
    if "Fantasy" in genre or "🏰" in genre:
        base_adventures["🌆 Urban Setting"] = "A magical city where wizards and merchants trade in equal measure"
        base_adventures["🌌 Mysterious Station"] = "A floating magical academy drifting through mystical realms"
    elif "Horror" in genre or "👻" in genre:
        base_adventures["🌲 Enchanted Forest"] = "A cursed woodland where the trees whisper unspeakable secrets"
        base_adventures["🌊 Pirate's Cove"] = "A ghost ship harbor where the dead refuse to rest"
        base_adventures["🌆 Urban Setting"] = "A haunted city where shadows move independently"
        base_adventures["🌌 Mysterious Station"] = "An abandoned research facility with a dark history"
    elif "Sci-Fi" in genre or "🚀" in genre:
        base_adventures["🏰 Cursed Castle"] = "An ancient alien fortress with mysterious technology"
        base_adventures["🐲 Dragon's Mountain"] = "A volcanic planet where mechanical beasts guard ancient tech"
        base_adventures["🌆 Urban Setting"] = "A sprawling space station at the crossroads of the galaxy"
        base_adventures["🌌 Mysterious Station"] = "A deep space research outpost that's gone silent"
    elif "Cyberpunk" in genre or "🤖" in genre:
        base_adventures["🏰 Cursed Castle"] = "A corporate megastructure that no one escapes"
        base_adventures["🌲 Enchanted Forest"] = "A virtual reality realm where code becomes reality"
        base_adventures["🌆 Urban Setting"] = "A neon-soaked metropolis ruled by corporate overlords"
        base_adventures["🌌 Mysterious Station"] = "An off-grid hacker haven hidden in cyberspace"
    elif "Comedy" in genre or "😂" in genre:
        base_adventures["🐲 Dragon's Mountain"] = "A mountain where a surprisingly friendly dragon runs a bed & breakfast"
        base_adventures["🏰 Cursed Castle"] = "A castle cursed with the most inconvenient magical mishaps"
        base_adventures["🌊 Pirate's Cove"] = "A pirate port where the most feared pirates... sell knitting supplies"
    return base_adventures

def standard_story_selector():
    st.markdown('<div class="chapter-title">🗺️ Choose Your Adventure Setting</div>', unsafe_allow_html=True)
    genre_info = GENRES[st.session_state.selected_genre]
    st.info(f"🎭 **{st.session_state.selected_genre}** - Adventures will have a {genre_info['tone']} tone focusing on {genre_info['themes']}")
    adventure_options = get_genre_adapted_adventures(st.session_state.selected_genre)
    for title, description in adventure_options.items():
        with st.expander(title):
            st.write(f"{description}, told in {genre_info['tone']} style.")
            if st.button(f"Start {title}", key=f"start_{title}"):
                st.session_state.selected_story = title
                st.session_state.story_selected = True
                st.session_state.is_custom_adventure = False
                initialize_adventure()
                st.rerun()

def custom_adventure_creator():
    st.markdown('<div class="chapter-title">🌟 Create Your Custom Adventure</div>', unsafe_allow_html=True)
    genre_info = GENRES[st.session_state.selected_genre]
    st.info(f"🎭 **{st.session_state.selected_genre}** - Your custom world will be told with {genre_info['tone']} tone and focus on {genre_info['themes']}")
    st.markdown('<div class="custom-world-section">', unsafe_allow_html=True)
    st.markdown("### 🎨 Design Your World")
    st.markdown(f"Create a unique setting for your adventure. The AI will adapt your world to fit the **{st.session_state.selected_genre}** genre style.")
    custom_option = st.radio("How would you like to create your world?",["Write world setting", "Upload world file"], horizontal=True)
    custom_world = ""
    if custom_option == "Write world setting":
        placeholder_text = f"""Describe your world in detail (it will be adapted to {st.session_state.selected_genre} style):
- Setting and locations (the AI will adapt these to fit {genre_info['tone']} tone)
- Key NPCs or factions
- Important rules or systems
- Plot hooks or mysteries
- Any specific elements you want included

Example for {st.session_state.selected_genre}: '{get_genre_example(st.session_state.selected_genre)}'"""
        custom_world = st.text_area("Describe your world setting:", placeholder=placeholder_text, height=200, help=f"The AI will interpret your world through the lens of {st.session_state.selected_genre}, emphasizing {genre_info['themes']}")
    else:
        uploaded_file = st.file_uploader("Upload world setting file", type=['txt', 'pdf'], help=f"Upload a .txt or .pdf file containing your world setting (will be adapted to {st.session_state.selected_genre} style)")
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain": custom_world = extract_text_from_txt(uploaded_file)
            elif uploaded_file.type == "application/pdf": custom_world = extract_text_from_pdf(uploaded_file)
            if custom_world:
                with st.expander("Preview uploaded world setting"): st.markdown(custom_world)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("🚀 Launch Custom Adventure", key="launch_custom"):
        if not custom_world.strip():
            st.error("Please provide a world setting description!")
        else:
            st.session_state.custom_world = custom_world.strip()
            st.session_state.selected_story = f"Custom {st.session_state.selected_genre} Adventure"
            st.session_state.story_selected = True
            st.session_state.is_custom_adventure = True
            initialize_adventure()
            st.success("Custom adventure initialized!")
            st.rerun()

def get_genre_example(genre):
    examples = { "🏰 Epic Fantasy": "A realm where ancient dragon lords once ruled, now their lost kingdoms hide powerful artifacts that could save or doom the world...", "🌑 Dark Fantasy": "A plague-ridden kingdom where the line between salvation and damnation blurs, and every victory comes at a terrible cost...", "👻 Horror": "An abandoned research facility where the lights went out three days ago, and the emergency broadcasts have gone silent...", "🚀 Sci-Fi Adventure": "A generation ship approaching an unknown star system after centuries of travel, with mysterious signals coming from the destination planet...", "🤖 Cyberpunk": "Neo-Tokyo 2087, where corporate arcologies scrape the toxic sky and underground hackers fight for digital freedom...", "😂 Comedy Adventure": "A magical academy where all the spells go hilariously wrong and the teachers are more confused than the students...", "🕵️ Mystery/Detective": "A locked-room murder in a mansion during a thunderstorm, where every guest has a secret and a motive...", "💖 Romance Adventure": "A matchmaking festival in a small town where old flames reunite and new connections spark unexpectedly..." }
    return examples.get(genre, "A unique world of your imagination...")


# ------------------------  Adventure Initialization  -------------------------
# MODIFIED: This function is completely rewritten for Gemini
def initialize_adventure():
    """Initialize the adventure with proper context using Google Gemini."""
    try:
        character = st.session_state.character
        backstory = st.session_state.character_backstory
        genre_info = GENRES[st.session_state.selected_genre]
        
        # Debug output
        st.write("🔧 Debug: Initializing adventure...")
        st.write(f"Character: {character}")
        st.write(f"Genre: {st.session_state.selected_genre}")
        
        # 1. Get the correct system prompt
        if st.session_state.is_custom_adventure:
            system_prompt = get_custom_system_prompt(character, st.session_state.custom_world, genre_info, backstory)
            initial_user_prompt = f"""
            {character['name']} the {character['class']} (background: {character['background']}) 
            begins their {st.session_state.selected_genre} adventure in this custom world. They carry their {character['starting_item']}.
            
            Create an engaging opening scene that introduces them to this world with {genre_info['tone']} tone, 
            focusing on {genre_info['themes']} themes, and establishes the initial atmosphere.
            Remember to write in second person and provide rich, immersive descriptions that fit the genre.
            """
        else:
            system_prompt = get_standard_system_prompt(character, st.session_state.selected_story, genre_info, backstory)
            initial_user_prompt = f"""
            {character['name']} the {character['class']} (background: {character['background']}) 
            begins their {st.session_state.selected_genre} adventure in {st.session_state.selected_story}. They carry their {character['starting_item']}.
            
            Set the opening scene with rich atmospheric detail that fits the {genre_info['tone']} tone, 
            incorporating {genre_info['themes']} themes, and provide the first set of choices.
            Remember to write in second person and create an immersive experience that matches the genre.
            """
            
        # 2. Configure Gemini and initialize the model with the system prompt
        st.write("🔧 Debug: Configuring Gemini...")
        
        # Check if API key exists
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("❌ Google API key not found in secrets!")
            return False
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.write(f"🔧 Debug: API key found (first 10 chars): {api_key[:10]}...")
        
        genai.configure(api_key=api_key)
        
        st.session_state.gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            system_instruction=system_prompt,
            generation_config={
                "temperature": 0.8,
                "max_output_tokens": 1500,
            }
        )
        
        st.write("🔧 Debug: Gemini model created successfully")
        
        # 3. Set the initial message history (without the system prompt)
        st.session_state.messages = [
            {"role": "user", "content": initial_user_prompt}
        ]
        
        st.write("🔧 Debug: Initial messages set")
        st.write(f"Messages: {len(st.session_state.messages)}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Failed to initialize adventure: {str(e)}")
        st.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        st.error(f"❌ Traceback: {traceback.format_exc()}")
        return False
# -----------------------------  Enhanced Sidebar  ----------------------------
# (No changes needed in this section)
def render_sidebar():
    with st.sidebar:
        if st.session_state.character_created:
            st.markdown('<div class="character-stats">', unsafe_allow_html=True)
            st.markdown("### 🛡️ Character Profile")
            st.markdown(f"**Name:** {st.session_state.character['name']}")
            st.markdown(f"**Class:** {st.session_state.character['class']}")
            st.markdown(f"**Background:** {st.session_state.character['background']}")
            st.markdown("</div>", unsafe_allow_html=True)
            if st.session_state.genre_selected:
                st.markdown(f"**🎭 Genre:** {st.session_state.selected_genre}")
            if st.session_state.character_backstory:
                with st.expander("📜 Character Backstory"):
                    st.markdown(f'<div class="backstory-section">{st.session_state.character_backstory}</div>', unsafe_allow_html=True)
            if st.session_state.story_selected:
                st.markdown(f"**⚔️ Adventure:** {st.session_state.selected_story}")
                st.markdown(f"**📖 Chapter:** {st.session_state.chapter_count}")
                st.markdown(f"**❤️ Health:** {st.session_state.health}/100")
                if st.session_state.inventory:
                    st.markdown("**🎒 Inventory:**")
                    for item in st.session_state.inventory: st.markdown(f"• {item}")
        st.markdown("---")
        st.markdown("### 🎮 Game Controls")
        if st.button("🔄 New Game", key="new_game"): new_game()
        if st.session_state.get("last_choice"): st.markdown(f"**Last Action:** {st.session_state.last_choice}")
        if st.session_state.story_selected and st.session_state.chapter_count > 0:
            st.markdown("### 📊 Adventure Log")
            if st.button("📋 Generate Session Summary"): generate_session_summary()
            if st.button("💾 Export Adventure"): export_adventure()
            if st.session_state.session_summaries:
                with st.expander("📚 Session Summaries"):
                    for i, summary in enumerate(st.session_state.session_summaries, 1): st.markdown(f"**Session {i}:** {summary}")


# ---------------------------  Session Management  ----------------------------
def new_game():
    """Reset all game state"""
    # Clear all session state except for any system keys we want to preserve
    keys_to_delete = []
    for key in st.session_state.keys():
        # Don't delete any Streamlit internal keys
        if not key.startswith('_'):
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del st.session_state[key]
    
    # Reinitialize the session state
    initialize_session_state()
    
    # Force a rerun to refresh the UI
    st.rerun()

# MODIFIED: Switched to Gemini for summary generation
def generate_session_summary():
    """Generate AI summary of current session using Gemini"""
    if len(st.session_state.messages) < 2:
        st.warning("Not enough content to summarize yet!")
        return
    
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash-latest") # Use a faster model for summaries

        recent_messages = st.session_state.messages[-6:]
        story_content = "\n\n".join([m["content"] for m in recent_messages if m["role"] in ["user", "assistant"]])
        
        summary_prompt = f"""
        Create a brief, engaging summary (2-3 sentences) of the recent adventure events:
        
        {story_content}
        
        Focus on key actions, discoveries, and character development. Write in past tense.
        """
        
        response = model.generate_content(
            summary_prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 150}
        )
        
        summary = response.text
        st.session_state.session_summaries.append(summary)
        st.success("Session summary generated!")
        
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")

# (No changes needed in export_adventure)
def export_adventure():
    character = st.session_state.character
    export_content = f"🧙 ADVENTURE EXPORT 🧙\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\nCHARACTER PROFILE:\nName: {character['name']}\nClass: {character['class']}\nBackground: {character['background']}\nStarting Item: {character['starting_item']}\n\n"
    if st.session_state.character_backstory: export_content += f"BACKSTORY:\n{st.session_state.character_backstory}\n\n"
    export_content += f"GENRE: {st.session_state.selected_genre}\nADVENTURE: {st.session_state.selected_story}\nTotal Chapters: {st.session_state.chapter_count}\nFinal Health: {st.session_state.health}/100\nFinal Inventory: {', '.join(st.session_state.inventory) if st.session_state.inventory else 'Empty'}\n\n"
    if st.session_state.session_summaries:
        export_content += "SESSION SUMMARIES:\n"
        for i, summary in enumerate(st.session_state.session_summaries, 1): export_content += f"{i}. {summary}\n"
        export_content += "\n"
    export_content += "COMPLETE ADVENTURE LOG:\n" + "="*50 + "\n\n"
    chapter_num = 1
    for message in st.session_state.messages[1:]:
        if message["role"] == "assistant":
            export_content += f"CHAPTER {chapter_num}:\n{message['content']}\n\n"
            chapter_num += 1
        elif message["role"] == "user":
            export_content += f"YOUR CHOICE: {message['content']}\n\n"
    st.download_button(label="📥 Download Adventure Log", data=export_content, file_name=f"adventure_{character['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain")

# ---------------------------  Enhanced AI Integration  -----------------------
# MODIFIED: This function is completely rewritten for Gemini
def call_ai(user_move: str) -> str:
    """Enhanced AI call using Google Gemini."""
    if not st.session_state.gemini_model:
        st.error("❌ Gemini model not initialized. Please start a new game.")
        return "The story cannot continue. Please start a new game."

    try:
        st.write(f"🔧 Debug: Calling AI with move: {user_move[:50]}...")
        
        # Append the new user move to the history
        st.session_state.messages.append({"role": "user", "content": user_move})

        # Reformat history for Gemini API: role 'assistant' becomes 'model'
        history_for_gemini = []
        for msg in st.session_state.messages:
            role = "model" if msg["role"] == "assistant" else "user"
            history_for_gemini.append({"role": role, "parts": [msg["content"]]})

        st.write(f"🔧 Debug: History length: {len(history_for_gemini)}")

        # Start a chat session from the model
        chat = st.session_state.gemini_model.start_chat(history=history_for_gemini[:-1])
        
        # Send the latest user message
        st.write("🔧 Debug: Sending message to Gemini...")
        response = chat.send_message(history_for_gemini[-1]['parts'][0])
        
        reply = response.text
        st.write(f"🔧 Debug: Received response: {reply[:100]}...")
        
        # Append AI's response to our internal message history
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        st.session_state.chapter_count += 1
        st.session_state.game_history.append(user_move)
        
        if st.session_state.chapter_count % 5 == 0:
            generate_session_summary()
        
        return reply
    
    except Exception as e:
        st.error(f"❌ AI Error: {str(e)}")
        st.error(f"❌ Error type: {type(e).__name__}")
        
        # More specific error handling
        if "API_KEY" in str(e):
            st.error("❌ API Key issue. Check your Google AI Studio API key.")
        elif "quota" in str(e).lower():
            st.error("❌ API quota exceeded. Check your usage limits.")
        elif "model" in str(e).lower():
            st.error("❌ Model error. The model might be unavailable.")
        
        # Remove the user message that caused the error to allow retrying
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
        
        return "The mystical forces of creation seem to be disrupted. Perhaps try a different action or rephrase your choice."


# ---------------------------  Enhanced Choice Parsing  -----------------------
# (No changes needed in this section)
def extract_choices(text):
    choice_patterns = [
        re.compile(r"^\s*(\d+)[\.)\-\s]+(.+)$", re.MULTILINE),
        re.compile(r"^\s*(\d+)\.\s*(.+)$", re.MULTILINE),
        re.compile(r"^\s*(\d+)\)\s*(.+)$", re.MULTILINE)
    ]
    choices = []
    for pattern in choice_patterns:
        matches = pattern.finditer(text)
        for match in matches:
            choice_text = match.group(2).strip()
            if choice_text and len(choice_text) > 10:
                if choice_text not in choices:
                    choices.append(choice_text)
    return choices[:4]

# ---------------------------  Main Game Interface  ---------------------------
# (No major changes needed, just logic flow adjustments)
def main_game():
    if not st.session_state.character_created:
        character_creator()
        return
    if not st.session_state.genre_selected:
        genre_selection()
        return
    if not hasattr(st.session_state, 'adventure_mode') or not st.session_state.adventure_mode:
        adventure_mode_selection()
        return
    if not st.session_state.story_selected:
        if st.session_state.adventure_mode == "standard":
            standard_story_selector()
        else:
            custom_adventure_creator()
        return

    # Debug output
    st.write("🔧 Debug: In main_game, story selected")
    st.write(f"🔧 Gemini model exists: {st.session_state.gemini_model is not None}")
    st.write(f"🔧 Messages count: {len(st.session_state.messages)}")

    # Check if we need to generate the first story response
    if (st.session_state.gemini_model and 
        len(st.session_state.messages) == 1 and 
        st.session_state.messages[0]["role"] == "user"):
        
        st.write("🔧 Debug: Generating first story response...")
        # First turn after initialization
        with st.spinner("🎭 Beginning your epic adventure with Gemini..."):
            initial_prompt = st.session_state.messages[0]['content']
            # We pop the user message so call_ai can add it back correctly
            st.session_state.messages.pop() 
            response = call_ai(initial_prompt)
            
            if response == "The story cannot continue. Please start a new game.":
                st.error("❌ Failed to start adventure. Check your API key and try again.")
                return
                
        st.rerun()
        return
    
    # If no model exists but story is selected, there was an initialization error
    if not st.session_state.gemini_model and st.session_state.story_selected:
        st.error("❌ Adventure initialization failed. Please try starting a new game.")
        if st.button("🔄 Retry Adventure Setup"):
            success = initialize_adventure()
            if success:
                st.success("✅ Adventure initialized successfully!")
                st.rerun()
        return
    
    # Display game messages
    chapter_num = 1
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "assistant":
            st.markdown(f'<div class="story-content">', unsafe_allow_html=True)
            st.markdown(f"### 📖 Chapter {chapter_num}")
            st.markdown(message["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            chapter_num += 1
        elif message["role"] == "user" and chapter_num > 1: # Don't show the initial hidden prompt
             st.markdown(f"**🎯 You chose:** *{message['content']}*")

    # Handle user input
    if st.session_state.gemini_model and len(st.session_state.messages) > 0:
        last_message = st.session_state.messages[-1]
        if last_message["role"] == "assistant":
            choices = extract_choices(last_message["content"])
            if choices:
                st.markdown("### 🎯 What do you do next?")
                cols = st.columns(min(len(choices), 2))
                for i, choice in enumerate(choices):
                    with cols[i % 2]:
                        if st.button(choice, key=f"choice_{i}", use_container_width=True):
                            st.session_state.last_choice = choice
                            with st.spinner("🎭 Weaving the next chapter of your tale..."):
                                call_ai(choice)
                            st.rerun()
            st.markdown("---")
            st.markdown("### ✨ Custom Action")
            if "custom_input_value" not in st.session_state: 
                st.session_state.custom_input_value = ""
            genre_info = GENRES[st.session_state.selected_genre]
            genre_placeholder = get_genre_action_placeholder(st.session_state.selected_genre)
            custom_action = st.text_input(
                "Describe your own action:", 
                value=st.session_state.custom_input_value, 
                placeholder=genre_placeholder, 
                key="custom_input_field", 
                help=f"Be specific and creative! The AI will adapt to your unique choices in {genre_info['tone']} style."
            )
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🎲 Take Action", key="custom_action_btn"):
                    if custom_action and custom_action.strip():
                        st.session_state.last_choice = custom_action
                        st.session_state.custom_input_value = ""
                        with st.spinner("🎭 Adapting to your creative choice..."):
                            call_ai(custom_action)
                        st.rerun()
                    else: 
                        st.warning("Please enter an action first!")
# (No changes needed in get_genre_action_placeholder)
def get_genre_action_placeholder(genre):
    placeholders = { "🏰 Epic Fantasy": "e.g., attempt to commune with the ancient spirits, challenge the dark lord to single combat, seek the blessing of the forest guardians", "🌑 Dark Fantasy": "e.g., make a deal with the shadowy figure, investigate the source of the corruption, sacrifice something precious for power", "👻 Horror": "e.g., carefully investigate the strange noise, barricade the door and wait, try to contact the outside world", "🚀 Sci-Fi Adventure": "e.g., scan the area with your tricorder, attempt to establish communication, analyze the alien technology", "🤖 Cyberpunk": "e.g., hack into the corporate mainframe, contact your underground connections, jack into the matrix", "😂 Comedy Adventure": "e.g., try an absurdly complicated plan, make a terrible pun to defuse tension, accidentally solve everything", "🕵️ Mystery/Detective": "e.g., examine the crime scene for clues, question the suspicious witness, check the alibis", "💖 Romance Adventure": "e.g., have a heartfelt conversation, plan a romantic gesture, address the relationship tension" }
    return placeholders.get(genre, "e.g., examine the surroundings closely, attempt to negotiate, search for alternative solutions")

# ---------------------------  App Entry Point  -------------------------------
if __name__ == "__main__":
    render_sidebar()
    main_game()