import re
import streamlit as st
from openai import OpenAI
import json
from datetime import datetime
import io
import PyPDF2
from typing import Optional

# ----------------------------------------------------------------------------- 
# Ultimate AI-powered Choose-Your-Own-Adventure with Advanced Features
# ----------------------------------------------------------------------------- 

# -----------------------------  Page setup  -----------------------------------
st.set_page_config(page_title="AI CYOA Adventure", page_icon="🧙", layout="wide")

# Custom CSS for better styling
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
    .session-summary {
        background: #e9ecef;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-title">🧙 Ultimate AI Choose Your Own Adventure</h1>', unsafe_allow_html=True)

# ------------------------  Enhanced System Prompts  ---------------------------
def get_standard_system_prompt(character, story_type, backstory=""):
    backstory_context = f"\n\nCharacter Backstory: {backstory}" if backstory else ""
    
    return f"""You are a master interactive fiction storyteller creating an immersive {story_type} adventure.

Character: {character['name']} the {character['class']} (Background: {character['background']}){backstory_context}

CRITICAL STORYTELLING RULES:
1. **Always write in SECOND PERSON** ("You approach the castle..." not "The character approaches...")
2. **2. **Write a full chapter of 900–1100 words** (~6–8 detailed paragraphs) with vivid sensory details. each chapter should be a complete richly developed scene.
3. **Use Markdown formatting**:
   - **Bold** for emphasis, important items, or dramatic moments
   - *Italics* for thoughts, whispers, magical effects, or atmospheric details
   - Create immersive, cinematic descriptions
4. **Always end with exactly 3-4 numbered choices**:
   1. [Detailed action description]
   2. [Detailed action description] 
   3. [Detailed action description]
   4. [Optional fourth choice]
5. **Maintain consistency** with previous choices and character development
6. **Include consequences** - choices should meaningfully impact the story
7. **Add atmospheric details** - sounds, smells, textures, emotions
8. **Reference inventory and character background** when relevant
9. **Create memorable NPCs** with distinct personalities and motivations
10. **Build tension and pacing** - vary between action, exploration, and character moments

Setting: {story_type}
Current Chapter: Continue the adventure maintaining narrative flow and character consistency.
"""

def get_custom_system_prompt(character, custom_setting, backstory=""):
    backstory_context = f"\n\nCharacter Backstory: {backstory}" if backstory else ""
    
    return f"""You are an expert interactive fiction storyteller adapting to a custom world setting.

Character: {character['name']} the {character['class']} (Background: {character['background']}){backstory_context}

Custom World Setting:
{custom_setting}

CRITICAL STORYTELLING RULES:
1. **Always write in SECOND PERSON** ("You step into..." not "The character steps...")
2. *2. **Write a full chapter of 900–1100 words** (~6–8 detailed paragraphs) with vivid sensory details. This must be a longer, richly developed scene.
3. **Use Markdown formatting**:
   - **Bold** for emphasis, important elements, or dramatic moments
   - *Italics* for thoughts, whispers, atmospheric effects, or mood
4. **Always end with exactly 3-4 numbered choices**:
   1. [Detailed action description]
   2. [Detailed action description]
   3. [Detailed action description] 
   4. [Optional fourth choice]
5. **Adapt to the custom setting** - respect the world's rules, tone, and atmosphere
6. **Maintain narrative consistency** with both the setting and previous choices
7. **Include rich atmospheric details** specific to this unique world
8. **Create meaningful consequences** for player decisions
9. **Reference character background** and how it fits in this custom world
10. **Build immersive scenes** that feel authentic to the provided setting

Current Chapter: Continue the adventure within this custom world, maintaining its unique flavor and rules.
"""

# ------------------------  File Processing Functions  -------------------------
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
        "adventure_mode": "",   # default “unset” so the selector always shows
        "custom_input_value": ""  # Add this line    
        }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ------------------------  Character Creator UI  -----------------------------
def character_creator():
    """Enhanced character creation with backstory support"""
    st.markdown('<div class="chapter-title">🎲 Create Your Character</div>', unsafe_allow_html=True)
    
    # Basic character info
    col1, col2 = st.columns(2)
    
    with col1:
        name = st.text_input("Character Name", placeholder="Enter your hero's name")
        character_class = st.selectbox(
            "Choose your class",
            ["Warrior", "Mage", "Rogue", "Cleric", "Ranger", "Paladin", "Bard", "Druid", "Warlock", "Monk"]
        )
    
    with col2:
        background = st.selectbox(
            "Character Background",
            ["Noble", "Commoner", "Merchant", "Scholar", "Outlaw", "Hermit", "Soldier", "Entertainer", "Criminal", "Folk Hero"]
        )
        starting_item = st.selectbox(
            "Starting Item",
            ["Ancient Sword", "Spell Tome", "Lockpicks", "Holy Symbol", "Bow & Arrows", "Mysterious Amulet", "Healing Potion", "Map Fragment"]
        )
    
    # Backstory section
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
    
    if st.button("🧩 Create Character", key="create_char"):
        if not name.strip():
            st.error("Please enter a character name!")
        else:
            st.session_state.character = {
                "name": name.strip(),
                "class": character_class,
                "background": background,
                "starting_item": starting_item,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.character_backstory = backstory
            st.session_state.inventory = [starting_item]
            st.session_state.character_created = True
            st.success(f"Character **{name} the {character_class}** created!")
            st.rerun()

# ------------------------  Adventure Mode Selection  -------------------------
def adventure_mode_selection():
    """Select between standard and custom adventure modes"""
    st.markdown('<div class="chapter-title">🗺️ Choose Adventure Mode</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🏰 Standard Adventures")
        st.markdown("Choose from pre-designed adventure settings with rich lore and established themes.")
        if st.button("🎯 Choose Standard Adventure", use_container_width=True):
            st.session_state.adventure_mode = "standard"
            st.rerun()
    
    with col2:
        st.markdown("### 🌟 Custom Adventure")
        st.markdown("Create or upload your own world setting for a completely unique experience.")
        if st.button("✨ Create Custom Adventure", use_container_width=True):
            st.session_state.adventure_mode = "custom"
            st.rerun()

# ------------------------  Standard Story Selector  -------------------------
def standard_story_selector():
    """Enhanced story selection interface"""
    st.markdown('<div class="chapter-title">🗺️ Choose Your Standard Adventure</div>', unsafe_allow_html=True)
    
    adventure_options = {
        "🌲 Enchanted Forest": "A mystical woodland where ancient magic flows through every tree, talking animals share ancient wisdom, and hidden fae courts plot in the shadows.",
        "🏰 Cursed Castle": "A dark fortress shrouded in perpetual mist, where shadows move independently, every door leads to mystery, and the dead do not rest easily.",
        "🐲 Dragon's Mountain": "A treacherous volcanic peak where a legendary wyrm guards treasures beyond imagination, and the very air crackles with draconic power.",
        "🌊 Pirate's Cove": "A lawless harbor where adventure and danger sail on every tide, treasure maps change hands like currency, and the sea holds countless secrets.",
        "🏜️ Desert Ruins": "Ancient temples buried in shifting sands, holding the secrets of a lost civilization whose magic still pulses through weathered stone.",
        "❄️ Frozen Wasteland": "An icy realm where survival is the first challenge, ancient evils slumber beneath the ice, and the aurora borealis whispers forgotten secrets.",
        "🌆 Steampunk City": "A city of brass and steam where clockwork automatons walk the streets, airships fill the sky, and industrial magic powers impossible inventions.",
        "🌌 Cosmic Station": "A space station on the edge of known space where alien species mingle, cosmic horrors lurk in the void, and technology defies comprehension."
    }
    
    for title, description in adventure_options.items():
        with st.expander(title):
            st.write(description)
            if st.button(f"Start {title}", key=f"start_{title}"):
                st.session_state.selected_story = title
                st.session_state.story_selected = True
                st.session_state.is_custom_adventure = False
                initialize_adventure()
                st.rerun()

# ------------------------  Custom Adventure Creator  -------------------------
def custom_adventure_creator():
    """Interface for creating custom adventures"""
    st.markdown('<div class="chapter-title">🌟 Create Your Custom Adventure</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-world-section">', unsafe_allow_html=True)
    st.markdown("### 🎨 Design Your World")
    st.markdown("Create a unique setting for your adventure. Be as creative as you want!")
    
    custom_option = st.radio(
        "How would you like to create your world?",
        ["Write world setting", "Upload world file"],
        horizontal=True
    )
    
    custom_world = ""
    
    if custom_option == "Write world setting":
        custom_world = st.text_area(
            "Describe your world setting:",
            placeholder="""Describe your world in detail:
- Setting and atmosphere (fantasy, sci-fi, modern, historical, etc.)
- Key locations and landmarks
- Important NPCs or factions
- Unique rules or magic systems
- Tone and themes
- Any specific plot hooks or mysteries

Example: 'A cyberpunk city where magic has returned to a high-tech world. Neon-lit streets are patrolled by corporate security drones while underground, hackers use technomancy to fight against mega-corporations...'""",
            height=200,
            help="The more detail you provide, the better the AI can create an immersive experience"
        )
    
    else:
        uploaded_file = st.file_uploader(
            "Upload world setting file",
            type=['txt', 'pdf'],
            help="Upload a .txt or .pdf file containing your world setting description"
        )
        
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain":
                custom_world = extract_text_from_txt(uploaded_file)
            elif uploaded_file.type == "application/pdf":
                custom_world = extract_text_from_pdf(uploaded_file)
            
            if custom_world:
                with st.expander("Preview uploaded world setting"):
                    st.markdown(custom_world)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("🚀 Launch Custom Adventure", key="launch_custom"):
        if not custom_world.strip():
            st.error("Please provide a world setting description!")
        else:
            st.session_state.custom_world = custom_world.strip()
            st.session_state.selected_story = "Custom Adventure"
            st.session_state.story_selected = True
            st.session_state.is_custom_adventure = True
            initialize_adventure()
            st.success("Custom adventure initialized!")
            st.rerun()

# ------------------------  Adventure Initialization  -------------------------
def initialize_adventure():
    """Initialize the adventure with proper context"""
    character = st.session_state.character
    backstory = st.session_state.character_backstory
    
    if st.session_state.is_custom_adventure:
        system_prompt = get_custom_system_prompt(character, st.session_state.custom_world, backstory)
        initial_prompt = f"""
        {character['name']} the {character['class']} (background: {character['background']}) 
        begins their adventure in this custom world. They carry their {character['starting_item']}.
        
        Create an engaging opening scene that introduces them to this world and establishes the initial atmosphere.
        Remember to write in second person and provide rich, immersive descriptions.
        """
    else:
        system_prompt = get_standard_system_prompt(character, st.session_state.selected_story, backstory)
        initial_prompt = f"""
        {character['name']} the {character['class']} (background: {character['background']}) 
        begins their adventure in {st.session_state.selected_story}. They carry their {character['starting_item']}.
        
        Set the opening scene with rich atmospheric detail and provide the first set of choices.
        Remember to write in second person and create an immersive experience.
        """
    
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_prompt}
    ]

# -----------------------------  Enhanced Sidebar  ----------------------------
def render_sidebar():
    """Enhanced sidebar with character stats and backstory"""
    with st.sidebar:
        if st.session_state.character_created:
            st.markdown('<div class="character-stats">', unsafe_allow_html=True)
            st.markdown("### 🛡️ Character Profile")
            st.markdown(f"**Name:** {st.session_state.character['name']}")
            st.markdown(f"**Class:** {st.session_state.character['class']}")
            st.markdown(f"**Background:** {st.session_state.character['background']}")
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Display backstory if available
            if st.session_state.character_backstory:
                with st.expander("📜 Character Backstory"):
                    st.markdown(f'<div class="backstory-section">{st.session_state.character_backstory}</div>', unsafe_allow_html=True)
            
            if st.session_state.story_selected:
                st.markdown(f"**⚔️ Adventure:** {st.session_state.selected_story}")
                st.markdown(f"**📖 Chapter:** {st.session_state.chapter_count}")
                st.markdown(f"**❤️ Health:** {st.session_state.health}/100")
                
                if st.session_state.inventory:
                    st.markdown("**🎒 Inventory:**")
                    for item in st.session_state.inventory:
                        st.markdown(f"• {item}")
        
        st.markdown("---")
        st.markdown("### 🎮 Game Controls")
        
        if st.button("🔄 New Game", key="new_game"):
            new_game()
        
        if st.session_state.get("last_choice"):
            st.markdown(f"**Last Action:** {st.session_state.last_choice}")
        
        # Export and summary features
        if st.session_state.story_selected and st.session_state.chapter_count > 0:
            st.markdown("### 📊 Adventure Log")
            
            if st.button("📋 Generate Session Summary"):
                generate_session_summary()
            
            if st.button("💾 Export Adventure"):
                export_adventure()
            
            if st.session_state.session_summaries:
                with st.expander("📚 Session Summaries"):
                    for i, summary in enumerate(st.session_state.session_summaries, 1):
                        st.markdown(f"**Session {i}:** {summary}")

# ---------------------------  Session Management  ----------------------------
def new_game():
    """Reset all game state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()
    st.rerun()

def generate_session_summary():
    """Generate AI summary of current session"""
    if len(st.session_state.messages) < 3:
        st.warning("Not enough content to summarize yet!")
        return
    
    try:
        client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or st.secrets["openai"]["OPENAI_API_KEY"])
        
        # Get recent story content
        recent_messages = st.session_state.messages[-6:]  # Last 6 messages
        story_content = "\n\n".join([m["content"] for m in recent_messages if m["role"] in ["user", "assistant"]])
        
        summary_prompt = f"""
        Create a brief, engaging summary (2-3 sentences) of the recent adventure events:
        
        {story_content}
        
        Focus on key actions, discoveries, and character development. Write in past tense.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        summary = response.choices[0].message.content
        st.session_state.session_summaries.append(summary)
        st.success("Session summary generated!")
        
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")

def export_adventure():
    """Export adventure as downloadable text file"""
    character = st.session_state.character
    
    # Build export content
    export_content = f"""
🧙 ADVENTURE EXPORT 🧙
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

CHARACTER PROFILE:
Name: {character['name']}
Class: {character['class']}
Background: {character['background']}
Starting Item: {character['starting_item']}

"""
    
    if st.session_state.character_backstory:
        export_content += f"BACKSTORY:\n{st.session_state.character_backstory}\n\n"
    
    export_content += f"""
ADVENTURE: {st.session_state.selected_story}
Total Chapters: {st.session_state.chapter_count}
Final Health: {st.session_state.health}/100
Final Inventory: {', '.join(st.session_state.inventory) if st.session_state.inventory else 'Empty'}

"""
    
    if st.session_state.session_summaries:
        export_content += "SESSION SUMMARIES:\n"
        for i, summary in enumerate(st.session_state.session_summaries, 1):
            export_content += f"{i}. {summary}\n"
        export_content += "\n"
    
    export_content += "COMPLETE ADVENTURE LOG:\n" + "="*50 + "\n\n"
    
    # Add all story messages
    chapter_num = 1
    for message in st.session_state.messages[1:]:  # Skip system message
        if message["role"] == "assistant":
            export_content += f"CHAPTER {chapter_num}:\n{message['content']}\n\n"
            chapter_num += 1
        elif message["role"] == "user":
            export_content += f"YOUR CHOICE: {message['content']}\n\n"
    
    # Create download
    st.download_button(
        label="📥 Download Adventure Log",
        data=export_content,
        file_name=f"adventure_{character['name']}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# ---------------------------  Enhanced AI Integration  -----------------------
def call_ai(user_move: str) -> str:
    """Enhanced AI call with better error handling and summaries"""
    try:
        client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY") or st.secrets["openai"]["OPENAI_API_KEY"])
        
        st.session_state.messages.append({"role": "user", "content": user_move})
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=st.session_state.messages,
            temperature=0.8,
            max_tokens=1500,  # Increased for longer chapters
            presence_penalty=0.1,
            frequency_penalty=0.1
        )
        
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        
        # Update chapter count and history
        st.session_state.chapter_count += 1
        st.session_state.game_history.append(user_move)
        
        # Auto-generate summaries every 5 chapters
        if st.session_state.chapter_count % 5 == 0:
            generate_session_summary()
        
        return reply
    
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        return "The mystical forces seem to be disrupted. Please try again in a moment."

# ---------------------------  Enhanced Choice Parsing  -----------------------
def extract_choices(text):
    """Enhanced choice extraction with better pattern matching"""
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
            if choice_text and len(choice_text) > 10:  # Filter out very short matches
                if choice_text not in choices:  # Avoid duplicates
                    choices.append(choice_text)
    
    return choices[:4]  # Limit to 4 choices max

# ---------------------------  Main Game Interface  ---------------------------
def main_game():
    """Enhanced main game interface"""
    if not st.session_state.character_created:
        character_creator()
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
    
    # Check if we need to generate the first story response
    # We have messages but no AI response yet
    if len(st.session_state.messages) == 2 and st.session_state.messages[1]["role"] == "user":
        # First turn - generate initial story
        with st.spinner("🎭 Beginning your epic adventure..."):
            call_ai("Begin the adventure with a compelling opening scene")
        st.rerun()
        return
    
    # Display game messages with enhanced formatting
    chapter_num = 1
    for i, message in enumerate(st.session_state.messages[1:], 1):
        if message["role"] == "assistant":
            st.markdown(f'<div class="story-content">', unsafe_allow_html=True)
            st.markdown(f"### 📖 Chapter {chapter_num}")
            st.markdown(message["content"])
            st.markdown('</div>', unsafe_allow_html=True)
            chapter_num += 1
        elif message["role"] == "user" and i > 1:
            st.markdown(f"**🎯 You chose:** *{message['content']}*")
    
    # Handle user input - only if we have AI responses
    if len(st.session_state.messages) > 2:  # System + initial prompt + at least one AI response
        last_ai_message = next((m["content"] for m in reversed(st.session_state.messages) 
                               if m["role"] == "assistant"), "")
        
        choices = extract_choices(last_ai_message)
        
        if choices:
            st.markdown("### 🎯 What do you do next?")
            
            # Create responsive columns for choices
            cols = st.columns(min(len(choices), 2))
            for i, choice in enumerate(choices):
                with cols[i % 2]:
                    if st.button(choice, key=f"choice_{i}", use_container_width=True):
                        st.session_state.last_choice = choice
                        with st.spinner("🎭 Weaving the next chapter of your tale..."):
                            call_ai(choice)
                        st.rerun()
        
        # Enhanced custom action input
        st.markdown("---")
        st.markdown("### ✨ Custom Action")
        
        # Initialize the input key in session state if it doesn't exist
        if "custom_input_value" not in st.session_state:
            st.session_state.custom_input_value = ""
        
        custom_action = st.text_input(
            "Describe your own action:",
            value=st.session_state.custom_input_value,
            placeholder="e.g., examine the ancient runes closely, attempt to negotiate with the dragon, search for secret passages",
            key="custom_input_field",
            help="Be specific and creative! The AI will adapt to your unique choices."
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🎲 Take Action", key="custom_action_btn"):
                if custom_action and custom_action.strip():
                    st.session_state.last_choice = custom_action
                    # Clear the input field by updating session state
                    st.session_state.custom_input_value = ""
                    with st.spinner("🎭 Adapting to your creative choice..."):
                        call_ai(custom_action)
                    st.rerun()
                else:
                    st.warning("Please enter an action first!")
    
    else:
        # First turn - generate initial story
        with st.spinner("🎭 Beginning your epic adventure..."):
            call_ai("Begin the adventure with a compelling opening scene")
        st.rerun()

# ---------------------------  App Entry Point  -------------------------------
if __name__ == "__main__":
    render_sidebar()
    main_game()