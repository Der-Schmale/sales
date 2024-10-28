import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

def scrape_mediamarkt(url):
    # Headers um den Scraper wie einen Browser erscheinen zu lassen
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Seite abrufen
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Listen für die Daten
        products = []
        old_prices = []
        new_prices = []
        
        # Produkt-Container finden
        product_containers = soup.find_all('div', class_='product-wrapper')
        
        for product in product_containers:
            # Produktname
            product_name = product.find('h2', class_='product-title')
            product_name = product_name.text.strip() if product_name else "N/A"
            
            # UVP (alter Preis)
            old_price = product.find('span', class_='strike-through')
            old_price = old_price.text.strip().replace('€', '').replace(',', '.') if old_price else "N/A"
            
            # Aktueller Preis
            new_price = product.find('span', class_='price')
            new_price = new_price.text.strip().replace('€', '').replace(',', '.') if new_price else "N/A"
            
            products.append(product_name)
            old_prices.append(old_price)
            new_prices.append(new_price)
        
        # DataFrame erstellen
        df = pd.DataFrame({
            'Produkt': products,
            'UVP': old_prices,
            'Angebotspreis': new_prices
        })
        
        return df
    
    except Exception as e:
        st.error(f"Fehler beim Scrapen: {str(e)}")
        return None

# Streamlit UI
st.title('🛍️ MediaMarkt Angebote Scraper')

# URL Eingabefeld
url = st.text_input('MediaMarkt URL eingeben:', 
                   'https://www.mediamarkt.de/de/campaign/angebote-aktionen')

if st.button('Angebote laden'):
    with st.spinner('Lade Angebote...'):
        # Scraping durchführen
        df = scrape_mediamarkt(url)
        
        if df is not None and not df.empty:
            # Daten anzeigen
            st.success(f'{len(df)} Produkte gefunden!')
            st.dataframe(df)
            
            # Download Button
            csv = df.to_csv(index=False).encode('utf-8')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="Als CSV herunterladen",
                data=csv,
                file_name=f'mediamarkt_angebote_{timestamp}.csv',
                mime='text/csv'
            )
            
            # Preisstatistiken
            if 'Angebotspreis' in df.columns:
                st.subheader('Preisstatistiken')
                df['Angebotspreis'] = pd.to_numeric(df['Angebotspreis'], errors='coerce')
                df['UVP'] = pd.to_numeric(df['UVP'], errors='coerce')
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Durchschnittlicher Angebotspreis", 
                             f"€{df['Angebotspreis'].mean():.2f}")
                with col2:
                    st.metric("Höchster Preis", 
                             f"€{df['Angebotspreis'].max():.2f}")
                with col3:
                    st.metric("Niedrigster Preis", 
                             f"€{df['Angebotspreis'].min():.2f}")
                
                # Durchschnittliche Ersparnis berechnen
                avg_savings = ((df['UVP'] - df['Angebotspreis']) / df['UVP'] * 100).mean()
                st.metric("Durchschnittliche Ersparnis", f"{avg_savings:.1f}%")
        else:
            st.warning('Keine Produkte gefunden. Bitte überprüfen Sie die URL und versuchen Sie es erneut.')

# Hilfe-Bereich
with st.expander("Hilfe & Informationen"):
    st.markdown("""
    ### Wie benutzt man den Scraper?
    1. Fügen Sie eine MediaMarkt Angebote-URL in das Textfeld ein
    2. Klicken Sie auf 'Angebote laden'
    3. Die gefundenen Produkte werden in einer Tabelle angezeigt
    4. Sie können die Daten als CSV-Datei herunterladen
    
    ### Hinweise
    - Bitte beachten Sie die Robot.txt und Nutzungsbedingungen von MediaMarkt
    - Fügen Sie Delays zwischen Anfragen ein, wenn Sie mehrere Seiten scrapen
    - Die Struktur der Website kann sich ändern, was zu Fehlern führen kann
    """)
