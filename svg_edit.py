
import streamlit as st
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import base64
import re

# Konfigurace stránky
st.set_page_config(
    page_title="SVG Zoo Editor",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styly
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .svg-container {
        border: 2px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        background: white;
        min-height: 400px;
    }
    
    .animal-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .animal-card:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    .animal-card-selected {
        background: linear-gradient(135deg, #20b2aa 0%, #008b8b 100%);
        border: 2px solid #ff6b35;
    }
    
    .config-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #3498db;
    }
    
    .animal-item {
        background: white;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border: 1px solid #ddd;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .progress-bar {
        background: #ddd;
        border-radius: 10px;
        overflow: hidden;
        height: 25px;
    }
    
    .progress-fill {
        background: linear-gradient(90deg, #3498db, #27ae60);
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        transition: width 0.3s ease;
    }
</style>
""", unsafe_allow_html=True)

# Session state inicializace
if 'svg_content' not in st.session_state:
    st.session_state.svg_content = None
if 'configurations' not in st.session_state:
    st.session_state.configurations = {}
if 'svg_elements' not in st.session_state:
    st.session_state.svg_elements = []
if 'selected_element' not in st.session_state:
    st.session_state.selected_element = None

def parse_svg_elements(svg_content):
    """Parsuje SVG a najde všechny klikací elementy"""
    try:
        root = ET.fromstring(svg_content)
        elements = []
        
        # Najít všechny relevantní elementy
        for elem in root.iter():
            if elem.tag.split('}')[-1] in ['g', 'path', 'polygon', 'circle', 'ellipse', 'rect']:
                element_id = elem.get('id', f"element_{len(elements)}")
                if not elem.get('id'):
                    elem.set('id', element_id)
                
                elements.append({
                    'id': element_id,
                    'tag': elem.tag.split('}')[-1],
                    'configured': element_id in st.session_state.configurations
                })
        
        return elements
    except Exception as e:
        st.error(f"Chyba při parsování SVG: {e}")
        return []

def get_animal_presets():
    """Přednastavené druhy zvířat"""
    return {
        '🦁': 'Lev',
        '🐘': 'Slon', 
        '🐅': 'Tygr',
        '🦒': 'Žirafa',
        '🦓': 'Zebra',
        '🐒': 'Opice',
        '🐧': 'Tučňák',
        '🦏': 'Nosorožec',
        '🦘': 'Klokan',
        '🐻': 'Medvěd',
        '🦜': 'Papoušek',
        '🐺': 'Vlk',
        '🦅': 'Orel',
        '🦉': 'Sova',
        '🐆': 'Gepard',
        '🦌': 'Jelen',
        '🐊': 'Krokodýl',
        '🐍': 'Had',
        '🦖': 'Dinosaurus',
        '🐧': 'Tučňák'
    }

def render_svg_with_highlights(svg_content, configurations):
    """Renderuje SVG s vizuálním zvýrazněním nakonfigurovaných elementů"""
    try:
        # Přidat CSS styling do SVG
        style_tag = """
        <style>
            .configured-element { 
                stroke: #27ae60 !important; 
                stroke-width: 3 !important; 
                opacity: 0.8;
            }
            .enclosure-pedestrian { fill: #90EE90 !important; }
            .enclosure-safari { fill: #FFD700 !important; }
            .path-pedestrian { fill: #DDA0DD !important; }
            .path-safari { fill: #F0E68C !important; }
            .water { fill: #87CEEB !important; }
            .restricted { fill: #FFB6C1 !important; }
            .facility { fill: #FFA500 !important; }
        </style>
        """
        
        # Vložit styling do SVG
        if '<svg' in svg_content and '<defs>' in svg_content:
            svg_content = svg_content.replace('<defs>', f'<defs>{style_tag}')
        elif '<svg' in svg_content:
            svg_content = svg_content.replace('<svg', f'<svg>{style_tag}<svg', 1).replace('<svg><svg', '<svg')
        
        # Přidat třídy k nakonfigurovaným elementům
        for element_id, config in configurations.items():
            if config.get('areaType'):
                pattern = f'id="{element_id}"'
                replacement = f'id="{element_id}" class="configured-element {config["areaType"]}"'
                svg_content = svg_content.replace(pattern, replacement)
        
        return svg_content
    except Exception as e:
        st.error(f"Chyba při renderování SVG: {e}")
        return svg_content

def main():
    st.markdown('<h1 class="main-header">🦁 SVG Zoo Editor 🦒</h1>', unsafe_allow_html=True)
    
    # Sidebar pro upload a základní ovládání
    with st.sidebar:
        st.header("📁 Nahrání SVG")
        
        # Upload SVG souboru
        uploaded_file = st.file_uploader(
            "Vyberte SVG soubor:",
            type=['svg'],
            help="Nahrajte vaši SVG mapu zoo"
        )
        
        if uploaded_file is not None:
            st.session_state.svg_content = uploaded_file.read().decode('utf-8')
            st.session_state.svg_elements = parse_svg_elements(st.session_state.svg_content)
            st.success("✅ SVG soubor načten!")
        
        # Progress bar
        if st.session_state.svg_elements:
            total = len(st.session_state.svg_elements)
            configured = len(st.session_state.configurations)
            progress = configured / total if total > 0 else 0
            
            st.markdown("### 📊 Pokrok konfigurace")
            st.markdown(f"""
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress*100}%">
                    {configured}/{total} ({progress*100:.0f}%)
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    if st.session_state.svg_content is None:
        st.info("👆 Nahrajte SVG soubor v bočním panelu pro začátek konfigurace")
        return
    
    # Hlavní layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ SVG Mapa")
        
        # Zobrazení SVG s lepším renderováním
        if st.session_state.svg_content:
            highlighted_svg = render_svg_with_highlights(
                st.session_state.svg_content, 
                st.session_state.configurations
            )
            
            # Alternativní způsoby zobrazení SVG
            display_method = st.radio(
                "Způsob zobrazení:",
                ["HTML", "Raw SVG", "Components"],
                horizontal=True,
                help="Zkuste různé způsoby pokud se mapa nezobrazuje správně"
            )
            
            if display_method == "HTML":
                # Metoda 1: HTML wrapper
                st.markdown(f"""
                <div style="width: 100%; height: 500px; border: 2px solid #ddd; border-radius: 10px; padding: 10px; background: white; overflow: auto;">
                    {highlighted_svg}
                </div>
                """, unsafe_allow_html=True)
                
            elif display_method == "Raw SVG":
                # Metoda 2: Přímé zobrazení
                st.image(highlighted_svg.encode('utf-8'), use_column_width=True)
                
            elif display_method == "Components":
                # Metoda 3: Components (pokud máte streamlit-components-v1)
                try:
                    import streamlit.components.v1 as components
                    components.html(f"""
                    <div style="width: 100%; height: 500px;">
                        {highlighted_svg}
                    </div>
                    """, height=500)
                except ImportError:
                    st.warning("Pro Components metodu nainstalujte: pip install streamlit-components-v1")
                    st.markdown(f"""
                    <div style="width: 100%; height: 500px; border: 2px solid #ddd; border-radius: 10px; padding: 10px; background: white; overflow: auto;">
                        {highlighted_svg}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Debug informace
            with st.expander("🔧 Debug informace"):
                st.text(f"SVG velikost: {len(st.session_state.svg_content)} znaků")
                st.text(f"Počet elementů: {len(st.session_state.svg_elements)}")
                st.text(f"Nakonfigurováno: {len(st.session_state.configurations)}")
                
                # Zobrazit začátek SVG
                st.code(st.session_state.svg_content[:500] + "...", language="xml")
        
        else:
            st.info("Nahrajte SVG soubor pro zobrazení mapy")
        
        # Seznam elementů pro výběr
        st.subheader("📋 Elementy na mapě")
        
        if st.session_state.svg_elements:
            # Filtrování
            show_all = st.checkbox("Zobrazit všechny elementy", value=True)
            
            elements_to_show = st.session_state.svg_elements
            if not show_all:
                elements_to_show = [e for e in st.session_state.svg_elements if not e['configured']]
            
            # Grid pro elementy
            cols = st.columns(4)
            for i, element in enumerate(elements_to_show):
                with cols[i % 4]:
                    config = st.session_state.configurations.get(element['id'], {})
                    
                    # Zobrazení elementu
                    display_name = config.get('enclosureName') or config.get('facilityName') or element['id']
                    icon = get_type_icon(config.get('areaType', ''))
                    
                    button_style = "animal-card-selected" if element['configured'] else "animal-card"
                    
                    if st.button(
                        f"{icon} {display_name}",
                        key=f"select_{element['id']}",
                        help=f"Konfigurovat {element['tag']} element"
                    ):
                        st.session_state.selected_element = element['id']
                        st.rerun()
    
    with col2:
        st.subheader("⚙️ Konfigurace")
        
        if st.session_state.selected_element:
            element_id = st.session_state.selected_element
            config = st.session_state.configurations.get(element_id, {})
            
            st.info(f"🎯 Konfigurujete: **{element_id}**")
            
            # Typ oblasti
            area_type = st.selectbox(
                "🏷️ Typ oblasti:",
                ["", "enclosure-pedestrian", "enclosure-safari", "path-pedestrian", 
                 "path-safari", "water", "restricted", "facility"],
                format_func=lambda x: {
                    "": "-- Vyberte typ --",
                    "enclosure-pedestrian": "🚶 Výběh - pěší část",
                    "enclosure-safari": "🚗 Výběh - safari",
                    "path-pedestrian": "🛤️ Cesta - pěší",
                    "path-safari": "🛣️ Cesta - safari", 
                    "water": "💧 Vodní plocha",
                    "restricted": "🚫 Zázemí zoo",
                    "facility": "🏢 Služba/budova"
                }.get(x, x),
                index=["", "enclosure-pedestrian", "enclosure-safari", "path-pedestrian", 
                       "path-safari", "water", "restricted", "facility"].index(config.get('areaType', '')) if config.get('areaType') in ["", "enclosure-pedestrian", "enclosure-safari", "path-pedestrian", "path-safari", "water", "restricted", "facility"] else 0
            )
            
            # Konfigurace výběhů
            if area_type and 'enclosure' in area_type:
                st.markdown("### 🏠 Konfigurace výběhu")
                
                enclosure_name = st.text_input(
                    "🏠 Název výběhu:",
                    value=config.get('enclosureName', ''),
                    placeholder="např. Africká savana, Ptačí svět"
                )
                
                enclosure_description = st.text_area(
                    "📝 Popis výběhu:",
                    value=config.get('enclosureDescription', ''),
                    height=80
                )
                
                zone = st.selectbox(
                    "🌍 Geografická oblast:",
                    ["Afrika", "Asie", "Evropa", "Amerika", "Austrálie", "Antarktida", "Světové"],
                    index=["Afrika", "Asie", "Evropa", "Amerika", "Austrálie", "Antarktida", "Světové"].index(config.get('zone', 'Afrika'))
                )
                
                # Časy krmení
                st.markdown("### 🕐 Časy krmení")
                feeding_times = config.get('feedingTimes', ['', '', ''])
                if len(feeding_times) < 3:
                    feeding_times.extend([''] * (3 - len(feeding_times)))
                
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    time1 = st.time_input("Čas 1", value=None, key=f"time1_{element_id}")
                with col_f2:
                    time2 = st.time_input("Čas 2", value=None, key=f"time2_{element_id}")
                with col_f3:
                    time3 = st.time_input("Čas 3", value=None, key=f"time3_{element_id}")
                
                # Správa zvířat
                st.markdown("### 🦁 Zvířata ve výběhu")
                
                # Aktuální zvířata
                current_animals = config.get('animals', [])
                
                if current_animals:
                    st.markdown("**Aktuální zvířata:**")
                    for i, animal in enumerate(current_animals):
                        col_a1, col_a2 = st.columns([4, 1])
                        with col_a1:
                            st.markdown(f"{animal['emoji']} **{animal['name']}**")
                        with col_a2:
                            if st.button("🗑️", key=f"remove_{element_id}_{i}", help="Odstranit"):
                                current_animals.pop(i)
                                config['animals'] = current_animals
                                st.session_state.configurations[element_id] = config
                                st.rerun()
                
                # Přidání nového zvířete
                st.markdown("**Přidat zvíře:**")
                
                # Rychlý výběr
                animal_presets = get_animal_presets()
                preset_cols = st.columns(5)
                for i, (emoji, name) in enumerate(list(animal_presets.items())[:10]):
                    with preset_cols[i % 5]:
                        if st.button(f"{emoji}", key=f"preset_{element_id}_{i}", help=name):
                            if 'animals' not in config:
                                config['animals'] = []
                            
                            # Kontrola duplikátů
                            if not any(a['name'] == name for a in config['animals']):
                                config['animals'].append({
                                    'name': name,
                                    'emoji': emoji,
                                    'id': len(config['animals'])
                                })
                                st.session_state.configurations[element_id] = config
                                st.rerun()
                
                # Ruční přidání
                col_n1, col_n2, col_n3 = st.columns([3, 1, 1])
                with col_n1:
                    new_animal_name = st.text_input("Název zvířete:", key=f"new_name_{element_id}")
                with col_n2:
                    new_animal_emoji = st.text_input("Emoji:", value="🐾", key=f"new_emoji_{element_id}")
                with col_n3:
                    if st.button("➕ Přidat", key=f"add_{element_id}"):
                        if new_animal_name:
                            if 'animals' not in config:
                                config['animals'] = []
                            
                            if not any(a['name'] == new_animal_name for a in config['animals']):
                                config['animals'].append({
                                    'name': new_animal_name,
                                    'emoji': new_animal_emoji,
                                    'id': len(config['animals'])
                                })
                                st.session_state.configurations[element_id] = config
                                st.rerun()
                            else:
                                st.error("Toto zvíře už je ve výběhu!")
                
                # Hromadné přidání
                bulk_text = st.text_area(
                    "📝 Hromadné přidání (každé zvíře na nový řádek):",
                    placeholder="🦜 Papoušek ara\n🦅 Orel mořský\n🦉 Sova lesní",
                    height=100,
                    key=f"bulk_{element_id}"
                )
                
                if st.button("📝 Přidat všechna zvířata", key=f"bulk_add_{element_id}"):
                    if bulk_text:
                        lines = bulk_text.strip().split('\n')
                        if 'animals' not in config:
                            config['animals'] = []
                        
                        added_count = 0
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                                
                            # Extrakce emoji a názvu
                            emoji_match = re.match(r'^([\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002600-\U000026FF\U00002700-\U000027BF]+)\s*(.+)', line)
                            if emoji_match:
                                emoji = emoji_match.group(1)
                                name = emoji_match.group(2)
                            else:
                                emoji = "🐾"
                                name = line
                            
                            # Kontrola duplikátů
                            if not any(a['name'] == name for a in config['animals']):
                                config['animals'].append({
                                    'name': name,
                                    'emoji': emoji,
                                    'id': len(config['animals'])
                                })
                                added_count += 1
                        
                        st.session_state.configurations[element_id] = config
                        st.success(f"✅ Přidáno {added_count} zvířat!")
                        st.rerun()
            
            # Konfigurace služeb
            elif area_type == 'facility':
                st.markdown("### 🏢 Konfigurace služby")
                
                facility_type = st.selectbox(
                    "Typ služby:",
                    ["WC", "Restaurant", "Shop", "Info", "FirstAid", "Parking"],
                    format_func=lambda x: {
                        "WC": "🚻 Toalety",
                        "Restaurant": "🍽️ Restaurace", 
                        "Shop": "🛍️ Obchod",
                        "Info": "ℹ️ Informace",
                        "FirstAid": "🏥 První pomoc",
                        "Parking": "🅿️ Parkování"
                    }.get(x, x),
                    index=["WC", "Restaurant", "Shop", "Info", "FirstAid", "Parking"].index(config.get('facilityType', 'WC'))
                )
                
                facility_name = st.text_input(
                    "📝 Název služby:",
                    value=config.get('facilityName', ''),
                    placeholder="např. Restaurace Safari"
                )
            
            # Uložení konfigurace
            if st.button("💾 Uložit konfiguraci", type="primary"):
                new_config = {
                    'areaType': area_type,
                    'elementId': element_id
                }
                
                if 'enclosure' in area_type:
                    new_config.update({
                        'enclosureName': enclosure_name,
                        'enclosureDescription': enclosure_description,
                        'zone': zone,
                        'feedingTimes': [t.strftime('%H:%M') for t in [time1, time2, time3] if t is not None],
                        'animals': config.get('animals', [])
                    })
                elif area_type == 'facility':
                    new_config.update({
                        'facilityType': facility_type,
                        'facilityName': facility_name
                    })
                
                st.session_state.configurations[element_id] = new_config
                
                # Označit element jako nakonfigurovaný
                for elem in st.session_state.svg_elements:
                    if elem['id'] == element_id:
                        elem['configured'] = True
                
                st.success("✅ Konfigurace uložena!")
                st.rerun()
            
            # Smazání konfigurace
            if element_id in st.session_state.configurations:
                if st.button("🗑️ Smazat konfiguraci", type="secondary"):
                    del st.session_state.configurations[element_id]
                    
                    # Označit jako nenakonfigurovaný
                    for elem in st.session_state.svg_elements:
                        if elem['id'] == element_id:
                            elem['configured'] = False
                    
                    st.success("🗑️ Konfigurace smazána!")
                    st.rerun()
        
        else:
            st.info("👆 Vyberte element na mapě pro konfiguraci")
    
    # Export sekce
    if st.session_state.configurations:
        st.markdown("---")
        st.subheader("📤 Export")
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            if st.button("📥 Stáhnout upravenou SVG", type="primary"):
                try:
                    # Zde by byl kód pro export SVG s interaktivitou
                    export_svg = generate_interactive_svg(
                        st.session_state.svg_content, 
                        st.session_state.configurations
                    )
                    
                    st.download_button(
                        label="💾 Stáhnout SVG soubor",
                        data=export_svg,
                        file_name=f"zoo_mapa_interaktivni_{datetime.now().strftime('%Y%m%d_%H%M')}.svg",
                        mime="image/svg+xml"
                    )
                except Exception as e:
                    st.error(f"Chyba při exportu: {e}")
        
        with col_e2:
            if st.button("📋 Export konfigurace JSON"):
                config_data = {
                    'timestamp': datetime.now().isoformat(),
                    'totalElements': len(st.session_state.svg_elements),
                    'configuredElements': len(st.session_state.configurations),
                    'configurations': st.session_state.configurations
                }
                
                st.download_button(
                    label="💾 Stáhnout JSON",
                    data=json.dumps(config_data, indent=2, ensure_ascii=False),
                    file_name=f"zoo_konfigurace_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json"
                )

def get_type_icon(area_type):
    """Vrátí ikonu pro typ oblasti"""
    icons = {
        'enclosure-pedestrian': '🚶',
        'enclosure-safari': '🚗',
        'path-pedestrian': '🛤️',
        'path-safari': '🛣️',
        'water': '💧',
        'restricted': '🚫',
        'facility': '🏢'
    }
    return icons.get(area_type, '❓')

def generate_interactive_svg(svg_content, configurations):
    """Generuje SVG s interaktivními atributy"""
    try:
        root = ET.fromstring(svg_content)
        
        # Přidat CSS styly pro interaktivitu
        style_element = ET.Element('style')
        style_element.text = """
        .enclosure { cursor: pointer; transition: all 0.3s ease; }
        .enclosure:hover .enclosure-area { 
            fill: #20b2aa !important; 
            stroke: #008b8b !important; 
            stroke-width: 4 !important; 
        }
        .enclosure:hover .animal-icon { opacity: 1 !important; }
        .animal-icon { opacity: 0; transition: all 0.3s ease; }
        """
        
        # Vložit style element na začátek SVG
        root.insert(0, style_element)
        
        # Přidat interaktivní atributy k nakonfigurovaným elementům
        for element_id, config in configurations.items():
            element = root.find(f".//*[@id='{element_id}']")
            if element is not None and config.get('areaType', '').startswith('enclosure'):
                
                # Převést element na skupinu pokud není
                if element.tag.split('}')[-1] != 'g':
                    group = ET.Element('g')
                    group.set('id', element_id + '_group')
                    parent = element.getparent()
                    parent.insert(list(parent).index(element), group)
                    parent.remove(element)
                    group.append(element)
                    element = group
                
                # Přidat atributy
                element.set('class', 'enclosure')
                element.set('data-enclosure', config.get('enclosureName', 'Výběh'))
                element.set('data-info', config.get('enclosureDescription', ''))
                element.set('data-zone', config.get('zone', ''))
                element.set('onclick', f"selectEnclosure('{element_id}')")
                
                # Přidat informace o zvířatech
                animals = config.get('animals', [])
                if animals:
                    animal_names = ', '.join([a['name'] for a in animals])
                    animal_emojis = ''.join([a['emoji'] for a in animals])
                    element.set('data-animals', animal_names)
                    element.set('data-animal-emojis', animal_emojis)
                    element.set('data-animal-count', str(len(animals)))
                
                # Přidat časy krmení
                feeding_times = config.get('feedingTimes', [])
                if feeding_times:
                    element.set('data-feeding-times', ', '.join(feeding_times))
        
        return ET.tostring(root, encoding='unicode')
        
    except Exception as e:
        st.error(f"Chyba při generování interaktivní SVG: {e}")
        return svg_content

if __name__ == "__main__":
    main()
