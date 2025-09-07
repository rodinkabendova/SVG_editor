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
        overflow: auto;
        max-height: 600px;
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
    
    .element-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 8px 12px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
        width: 100%;
        margin: 2px 0;
        text-align: left;
    }
    
    .element-button:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    
    .element-button-configured {
        background: linear-gradient(135deg, #20b2aa 0%, #008b8b 100%);
        border: 2px solid #ff6b35;
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
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag_name in ['g', 'path', 'polygon', 'circle', 'ellipse', 'rect']:
                element_id = elem.get('id', f"element_{len(elements)}")
                if not elem.get('id'):
                    elem.set('id', element_id)
                
                elements.append({
                    'id': element_id,
                    'tag': tag_name,
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
        '🐙': 'Chobotnice'
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
            # Najít první výskyt <svg> a vložit styl za něj
            svg_start = svg_content.find('<svg')
            svg_end = svg_content.find('>', svg_start)
            if svg_end != -1:
                svg_content = svg_content[:svg_end+1] + style_tag + svg_content[svg_end+1:]
        
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
            
            # Test zobrazení SVG
            with st.expander("🔍 Test zobrazení SVG"):
                st.markdown("**Náhled prvních 500 znaků:**")
                preview = st.session_state.svg_content[:500]
                st.code(preview, language="xml")
                
                # Rychlý test validity
                if st.session_state.svg_content.strip().startswith('<'):
                    st.success("✅ Soubor začíná XML/HTML tagem")
                else:
                    st.warning("⚠️ Soubor nezačíná XML tagem")
                
                if '<svg' in st.session_state.svg_content:
                    st.success("✅ Obsahuje SVG tag")
                else:
                    st.error("❌ Neobsahuje SVG tag")
                
                # Test velikosti
                size_mb = len(st.session_state.svg_content) / (1024 * 1024)
                if size_mb > 5:
                    st.warning(f"⚠️ Velký soubor: {size_mb:.1f} MB")
                else:
                    st.info(f"📏 Velikost: {size_mb:.2f} MB")
            
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
        
        # Import/Export konfigurace
        st.markdown("---")
        st.header("💾 Import/Export")
        
        # Import konfigurace
        config_file = st.file_uploader(
            "Import konfigurace:",
            type=['json'],
            help="Nahrajte dříve uložený JSON s konfigurací"
        )
        
        if config_file is not None:
            try:
                config_data = json.loads(config_file.read().decode('utf-8'))
                if 'configurations' in config_data:
                    st.session_state.configurations = config_data['configurations']
                    # Aktualizovat označení elementů
                    for elem in st.session_state.svg_elements:
                        elem['configured'] = elem['id'] in st.session_state.configurations
                    st.success("✅ Konfigurace importována!")
                    st.rerun()
            except Exception as e:
                st.error(f"Chyba při importu: {e}")
    
    if st.session_state.svg_content is None:
        st.info("👆 Nahrajte SVG soubor v bočním panelu pro začátek konfigurace")
        
        # Ukázková sekce
        st.markdown("---")
        st.subheader("🎯 Co tento editor umí:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            **🗺️ Vizualizace SVG map**
            - Načítání SVG souborů
            - Interaktivní zvýraznění
            - Vícenásobné zobrazovací režimy
            """)
        
        with col2:
            st.markdown("""
            **⚙️ Konfigurace oblastí**
            - Výběhy s detaily zvířat
            - Cesty a vodní plochy
            - Služby a budovy
            """)
        
        with col3:
            st.markdown("""
            **📤 Export dat**
            - Interaktivní SVG soubory
            - JSON konfigurace
            - Import/Export nastavení
            """)
        
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
            
            # Způsob zobrazení SVG
            display_method = st.radio(
                "Způsob zobrazení:",
                ["HTML", "Components"],
                horizontal=True,
                help="Zkuste různé způsoby pokud se mapa nezobrazuje správně"
            )
            
            if display_method == "HTML":
                # HTML wrapper s lepším stylováním
                st.markdown(f"""
                <div class="svg-container">
                    {highlighted_svg}
                </div>
                """, unsafe_allow_html=True)
                
            elif display_method == "Components":
                # Použití vestavěných Streamlit komponent
                import streamlit.components.v1 as components
                components.html(f"""
                <div style="width: 100%; height: 500px; overflow: auto; border: 2px solid #ddd; border-radius: 10px; padding: 10px; background: white;">
                    {highlighted_svg}
                </div>
                """, height=520)
            
            # Debug informace
            with st.expander("🔧 Debug informace"):
                st.text(f"SVG velikost: {len(st.session_state.svg_content)} znaků")
                st.text(f"Počet elementů: {len(st.session_state.svg_elements)}")
                st.text(f"Nakonfigurováno: {len(st.session_state.configurations)}")
                
                # Zobrazit začátek SVG
                st.code(st.session_state.svg_content[:500] + "...", language="xml")
        
        # Seznam elementů pro výběr
        st.subheader("📋 Elementy na mapě")
        
        if st.session_state.svg_elements:
            # Filtrování
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                show_all = st.checkbox("Zobrazit všechny elementy", value=True)
            with filter_col2:
                search_term = st.text_input("🔍 Hledat element:", placeholder="Zadejte název...")
            
            elements_to_show = st.session_state.svg_elements
            if not show_all:
                elements_to_show = [e for e in st.session_state.svg_elements if not e['configured']]
            
            if search_term:
                elements_to_show = [e for e in elements_to_show if search_term.lower() in e['id'].lower()]
            
            # Grid pro elementy s lepším zobrazením
            if elements_to_show:
                st.markdown(f"**Zobrazeno {len(elements_to_show)} elementů:**")
                
                # Rozdělení do sloupců
                num_cols = 3
                cols = st.columns(num_cols)
                
                for i, element in enumerate(elements_to_show):
                    with cols[i % num_cols]:
                        config = st.session_state.configurations.get(element['id'], {})
                        
                        # Zobrazení elementu
                        display_name = (config.get('enclosureName') or 
                                      config.get('facilityName') or 
                                      element['id'])
                        icon = get_type_icon(config.get('areaType', ''))
                        
                        # Vytvoření tlačítka
                        button_text = f"{icon} {display_name}"
                        if len(button_text) > 25:
                            button_text = button_text[:22] + "..."
                        
                        if st.button(
                            button_text,
                            key=f"select_{element['id']}",
                            help=f"Konfigurovat {element['tag']} element\nID: {element['id']}",
                            use_container_width=True
                        ):
                            st.session_state.selected_element = element['id']
                            st.rerun()
                        
                        # Indikátor konfigurace
                        if element['configured']:
                            st.markdown("✅ *Nakonfigurováno*")
                        else:
                            st.markdown("⚙️ *Čeká na konfiguraci*")
            else:
                st.info("Žádné elementy nevyhovují filtru")
    
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
                feeding_times = config.get('feedingTimes', [])
                
                # Dynamické přidávání časů
                if 'temp_feeding_times' not in st.session_state:
                    st.session_state.temp_feeding_times = feeding_times if feeding_times else ['']
                
                for i in range(len(st.session_state.temp_feeding_times)):
                    col_time, col_remove = st.columns([4, 1])
                    with col_time:
                        time_val = st.time_input(
                            f"Čas {i+1}:", 
                            value=None,
                            key=f"feeding_time_{element_id}_{i}"
                        )
                        if time_val:
                            while len(st.session_state.temp_feeding_times) <= i:
                                st.session_state.temp_feeding_times.append('')
                            st.session_state.temp_feeding_times[i] = time_val.strftime('%H:%M')
                    with col_remove:
                        if len(st.session_state.temp_feeding_times) > 1:
                            if st.button("🗑️", key=f"remove_time_{element_id}_{i}"):
                                st.session_state.temp_feeding_times.pop(i)
                                st.rerun()
                
                if st.button("➕ Přidat čas krmení"):
                    st.session_state.temp_feeding_times.append('')
                    st.rerun()
                
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
                
                # Přidání nového zvířete - rychlý výběr
                st.markdown("**Rychlý výběr zvířat:**")
                animal_presets = get_animal_presets()
                
                # Zobrazit presety v gridu
                preset_items = list(animal_presets.items())
                num_cols = 5
                for row in range(0, len(preset_items), num_cols):
                    cols = st.columns(num_cols)
                    for col_idx, (emoji, name) in enumerate(preset_items[row:row+num_cols]):
                        with cols[col_idx]:
                            if st.button(f"{emoji}", key=f"preset_{element_id}_{row}_{col_idx}", help=name):
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
                                else:
                                    st.error("Toto zvíře už je ve výběhu!")
                
                # Ruční přidání
                st.markdown("**Ruční přidání:**")
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
            
            # Konfigurace ostatních typů
            elif area_type in ['path-pedestrian', 'path-safari', 'water', 'restricted']:
                st.markdown(f"### {get_type_icon(area_type)} Konfigurace oblasti")
                
                area_name = st.text_input(
                    "📝 Název oblasti:",
                    value=config.get('areaName', ''),
                    placeholder="např. Hlavní cesta, Jezero, Zázemí"
                )
                
                area_description = st.text_area(
                    "📝 Popis:",
                    value=config.get('areaDescription', ''),
                    height=60
                )
            
            # Uložení konfigurace
            if area_type and st.button("💾 Uložit konfiguraci", type="primary"):
                new_config = {
                    'areaType': area_type,
                    'elementId': element_id
                }
                
                if 'enclosure' in area_type:
                    # Zpracování feeding times
                    feeding_times_clean = [t for t in st.session_state.temp_feeding_times if t]
                    
                    new_config.update({
                        'enclosureName': enclosure_name,
                        'enclosureDescription': enclosure_description,
                        'zone': zone,
                        'feedingTimes': feeding_times_clean,
                        'animals': config.get('animals', [])
                    })
                elif area_type == 'facility':
                    new_config.update({
                        'facilityType': facility_type,
                        'facilityName': facility_name
                    })
                elif area_type in ['path-pedestrian', 'path-safari', 'water', 'restricted']:
                    new_config.update({
                        'areaName': area_name,
                        'areaDescription': area_description
                    })
                
                st.session_state.configurations[element_id] = new_config
                
                # Označit element jako nakonfigurovaný
                for elem in st.session_state.svg_elements:
                    if elem['id'] == element_id:
                        elem['configured'] = True
                
                # Vyčistit temp feeding times
                if 'temp_feeding_times' in st.session_state:
                    del st.session_state.temp_feeding_times
                
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
                    
                    # Vyčistit temp feeding times
                    if 'temp_feeding_times' in st.session_state:
                        del st.session_state.temp_feeding_times
                    
                    st.success("🗑️ Konfigurace smazána!")
                    st.rerun()
        
        else:
            st.info("👆 Vyberte element na mapě pro konfiguraci")
            
            # Přehled nakonfigurovaných elementů
            if st.session_state.configurations:
                st.markdown("### 📊 Nakonfigurované elementy")
                for element_id, config in st.session_state.configurations.items():
                    icon = get_type_icon(config.get('areaType', ''))
                    name = (config.get('enclosureName') or 
                           config.get('facilityName') or 
                           config.get('areaName') or 
                           element_id)
                    
                    if st.button(f"{icon} {name}", key=f"overview_{element_id}"):
                        st.session_state.selected_element = element_id
                        st.rerun()
    
    # Export sekce
    if st.session_state.configurations:
        st.markdown("---")
        st.subheader("📤 Export")
        
        col_e1, col_e2 = st.columns(2)
        
        with col_e1:
            if st.button("📥 Stáhnout upravenou SVG", type="primary"):
                try:
                    # Generovat interaktivní SVG
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
        
        # Statistiky
        st.markdown("### 📊 Statistiky konfigurace")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        with col_s1:
            total_elements = len(st.session_state.svg_elements)
            st.metric("📋 Celkem elementů", total_elements)
        
        with col_s2:
            configured_elements = len(st.session_state.configurations)
            st.metric("⚙️ Nakonfigurováno", configured_elements)
        
        with col_s3:
            enclosures = len([c for c in st.session_state.configurations.values() 
                            if c.get('areaType', '').startswith('enclosure')])
            st.metric("🏠 Výběhy", enclosures)
        
        with col_s4:
            total_animals = sum([len(c.get('animals', [])) for c in st.session_state.configurations.values()])
            st.metric("🦁 Zvířata", total_animals)

def create_interactive_svg_html(svg_content, svg_elements):
    """Vytvoří interaktivní HTML s SVG, které umožňuje klikání na elementy"""
    
    # Seznam všech ID elementů pro JavaScript
    element_ids = [elem['id'] for elem in svg_elements]
    element_ids_js = json.dumps(element_ids)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 10px;
                font-family: Arial, sans-serif;
                background: #f8f9fa;
            }}
            
            .svg-container {{
                border: 2px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                background: white;
                overflow: auto;
                max-height: 480px;
            }}
            
            .clickable-element {{
                cursor: pointer !important;
                transition: all 0.3s ease;
            }}
            
            .clickable-element:hover {{
                stroke: #ff6b35 !important;
                stroke-width: 4 !important;
                opacity: 0.8 !important;
            }}
            
            .selected-element {{
                stroke: #ff6b35 !important;
                stroke-width: 4 !important;
                fill: #ffeb3b !important;
                opacity: 0.7 !important;
            }}
            
            .info-panel {{
                position: fixed;
                top: 10px;
                right: 10px;
                background: white;
                border: 2px solid #333;
                border-radius: 10px;
                padding: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 1000;
                max-width: 250px;
                font-size: 14px;
            }}
            
            .close-btn {{
                background: #ff4444;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                cursor: pointer;
                float: right;
            }}
            
            .select-btn {{
                background: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                cursor: pointer;
                margin-top: 10px;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="svg-container">
            {svg_content}
        </div>
        
        <script>
            let selectedElement = null;
            const elementIds = {element_ids_js};
            
            // Přidat event listenery ke všem elementům
            document.addEventListener('DOMContentLoaded', function() {{
                elementIds.forEach(function(id) {{
                    const element = document.getElementById(id);
                    if (element) {{
                        element.classList.add('clickable-element');
                        element.addEventListener('click', function(e) {{
                            e.stopPropagation();
                            selectElement(id, element);
                        }});
                    }}
                }});
                
                // Kliknutí mimo elementy zruší výběr
                document.addEventListener('click', function(e) {{
                    if (!e.target.closest('.clickable-element') && !e.target.closest('.info-panel')) {{
                        clearSelection();
                    }}
                }});
            }});
            
            function selectElement(elementId, element) {{
                // Zrušit předchozí výběr
                clearSelection();
                
                // Označit nový element
                selectedElement = element;
                element.classList.add('selected-element');
                
                // Zobrazit info panel
                showInfoPanel(elementId);
                
                // Poslat info do Streamlit (simulace)
                console.log('Selected element:', elementId);
            }}
            
            function clearSelection() {{
                if (selectedElement) {{
                    selectedElement.classList.remove('selected-element');
                    selectedElement = null;
                }}
                hideInfoPanel();
            }}
            
            function showInfoPanel(elementId) {{
                // Odstranit existující panel
                hideInfoPanel();
                
                // Vytvořit nový panel
                const panel = document.createElement('div');
                panel.className = 'info-panel';
                panel.id = 'info-panel';
                
                panel.innerHTML = `
                    <button class="close-btn" onclick="clearSelection()">×</button>
                    <h4>📍 Element vybrán</h4>
                    <p><strong>ID:</strong> ${{elementId}}</p>
                    <p><strong>Typ:</strong> ${{getElementType(elementId)}}</p>
                    <button class="select-btn" onclick="selectForConfiguration('${{elementId}}')">
                        🎯 Konfigurovat element
                    </button>
                `;
                
                document.body.appendChild(panel);
            }}
            
            function hideInfoPanel() {{
                const panel = document.getElementById('info-panel');
                if (panel) {{
                    panel.remove();
                }}
            }}
            
            function getElementType(elementId) {{
                const element = document.getElementById(elementId);
                if (!element) return 'Neznámý';
                
                const tagName = element.tagName.toLowerCase();
                const className = element.className.baseVal || element.className || '';
                
                if (className.includes('enclosure')) return '🏠 Výběh';
                if (className.includes('facility')) return '🏢 Služba';
                if (className.includes('path')) return '🛤️ Cesta';
                if (className.includes('water')) return '💧 Voda';
                if (className.includes('restricted')) return '🚫 Zázemí';
                
                return `📐 ${{tagName}}`;
            }}
            
            function selectForConfiguration(elementId) {{
                // Zde by bylo volání do Streamlit
                alert(`Element "${{elementId}}" vybrán pro konfiguraci!\\n\\nV reálné aplikaci by se otevřel konfigurační panel.`);
                
                // Simulace - poslat data do parent window
                if (window.parent) {{
                    window.parent.postMessage({{
                        type: 'elementSelected',
                        elementId: elementId
                    }}, '*');
                }}
            }}
            
            // Zvýraznit všechny klikací elementy při načtení
            setTimeout(function() {{
                elementIds.forEach(function(id) {{
                    const element = document.getElementById(id);
                    if (element) {{
                        // Přidat jemné zvýraznění
                        const originalStroke = element.getAttribute('stroke') || 'none';
                        const originalStrokeWidth = element.getAttribute('stroke-width') || '1';
                        
                        if (originalStroke === 'none') {{
                            element.setAttribute('stroke', '#cccccc');
                            element.setAttribute('stroke-width', '1');
                        }}
                    }}
                }});
            }}, 500);
        </script>
    </body>
    </html>
    """
    
    return html_content

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
    """Generuje SVG s interaktivními atributy a JavaScript funkcionalitou"""
    try:
        root = ET.fromstring(svg_content)
        
        # Přidat CSS styly pro interaktivitu
        style_element = ET.Element('style')
        style_element.text = """
        .enclosure { 
            cursor: pointer; 
            transition: all 0.3s ease; 
        }
        .enclosure:hover .enclosure-area { 
            fill: #20b2aa !important; 
            stroke: #008b8b !important; 
            stroke-width: 4 !important; 
        }
        .enclosure:hover .animal-icon { 
            opacity: 1 !important; 
        }
        .animal-icon { 
            opacity: 0; 
            transition: all 0.3s ease; 
        }
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
        
        .info-popup {
            position: fixed;
            background: white;
            border: 2px solid #333;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 1000;
            max-width: 300px;
            font-family: Arial, sans-serif;
        }
        """
        
        # Přidat JavaScript pro interaktivitu
        script_element = ET.Element('script')
        script_element.text = """
        function selectEnclosure(elementId) {
            // Zobrazit informace o výběhu
            var element = document.getElementById(elementId);
            if (!element) return;
            
            var enclosureName = element.getAttribute('data-enclosure') || 'Neznámý výběh';
            var animals = element.getAttribute('data-animals') || 'Žádná zvířata';
            var animalEmojis = element.getAttribute('data-animal-emojis') || '';
            var feedingTimes = element.getAttribute('data-feeding-times') || 'Neurčeno';
            var zone = element.getAttribute('data-zone') || '';
            
            // Vytvořit popup
            var popup = document.createElement('div');
            popup.className = 'info-popup';
            popup.innerHTML = 
                '<h3>' + animalEmojis + ' ' + enclosureName + '</h3>' +
                '<p><strong>Oblast:</strong> ' + zone + '</p>' +
                '<p><strong>Zvířata:</strong> ' + animals + '</p>' +
                '<p><strong>Krmení:</strong> ' + feedingTimes + '</p>' +
                '<button onclick="closePopup()" style="margin-top:10px; padding:5px 10px; background:#3498db; color:white; border:none; border-radius:5px; cursor:pointer;">Zavřít</button>';
            
            // Umístit popup
            popup.style.left = '50px';
            popup.style.top = '50px';
            
            // Odstranit předchozí popup
            var existingPopup = document.querySelector('.info-popup');
            if (existingPopup) {
                existingPopup.remove();
            }
            
            document.body.appendChild(popup);
        }
        
        function closePopup() {
            var popup = document.querySelector('.info-popup');
            if (popup) {
                popup.remove();
            }
        }
        
        // Zavřít popup při kliknutí mimo
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.enclosure') && !e.target.closest('.info-popup')) {
                closePopup();
            }
        });
        """
        
        # Vložit style a script elementy na začátek SVG
        root.insert(0, style_element)
        root.insert(1, script_element)
        
        # Přidat interaktivní atributy k nakonfigurovaným elementům
        for element_id, config in configurations.items():
            element = root.find(f".//*[@id='{element_id}']")
            if element is not None:
                # Přidat základní třídy
                area_type = config.get('areaType', '')
                element.set('class', f'configured-element {area_type}')
                
                if area_type.startswith('enclosure'):
                    # Převést element na skupinu pokud není
                    tag_name = element.tag.split('}')[-1] if '}' in element.tag else element.tag
                    if tag_name != 'g':
                        group = ET.Element('g')
                        group.set('id', element_id + '_group')
                        group.set('class', f'enclosure configured-element {area_type}')
                        parent = element.getparent()
                        if parent is not None:
                            parent.insert(list(parent).index(element), group)
                            parent.remove(element)
                            group.append(element)
                            element = group
                    else:
                        element.set('class', f'enclosure configured-element {area_type}')
                    
                    # Přidat atributy
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
                
                elif area_type == 'facility':
                    element.set('data-facility-type', config.get('facilityType', ''))
                    element.set('data-facility-name', config.get('facilityName', 'Služba'))
                    element.set('onclick', f"alert('Služba: {config.get('facilityName', 'Neznámá služba')}')")
        
        return ET.tostring(root, encoding='unicode')
        
    except Exception as e:
        st.error(f"Chyba při generování interaktivní SVG: {e}")
        return svg_content

if __name__ == "__main__":
    main()
