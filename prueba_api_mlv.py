import requests

def buscar_en_mlv(producto_query, tasa_bcv=None):
    """
    Hace una petición a la API pública de Mercado Libre Venezuela.
    Filtra por condición 'nuevo' y extrae el precio en USD.
    """
    url = "https://api.mercadolibre.com/sites/MLV/search"
    params = {
        "q": producto_query,
        "condition": "new",  # Solo artículos nuevos
        "limit": 20          # Traer los 20 más relevantes
    }
    
    # 🥷 EL DISFRAZ: Le decimos a ML que somos un navegador Chrome real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9"
    }
    
    print(f"\n🔍 Buscando '{producto_query}' en Mercado Libre Venezuela...")
    
    try:
        # Aquí pasamos los headers en la petición
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() # Verifica que no haya error http
        data = response.json()
    except Exception as e:
        print(f"❌ Error al conectar con la API: {e}")
        return

    resultados = data.get("results", [])
    
    if not resultados:
        print("📭 No se encontraron resultados para esta búsqueda.")
        return

    articulos_validos = []
    
    for item in resultados:
        titulo = item.get("title")
        precio_raw = float(item.get("price", 0))
        moneda = item.get("currency_id") # 'USD' o 'VES'
        
        # ── Conversión de moneda ──
        precio_usd = 0.0
        if moneda == "USD":
            precio_usd = precio_raw
        elif moneda == "VES":
            if tasa_bcv and tasa_bcv > 0:
                precio_usd = precio_raw / tasa_bcv
            else:
                continue
                
        if precio_usd > 0:
            articulos_validos.append({
                "titulo": titulo,
                "precio": precio_usd,
                "moneda_original": moneda
            })

    # ── Mostrar Resultados ──
    print(f"\n📊 TOP 10 RESULTADOS ENCONTRADOS (Moneda unificada a USD):")
    print("-" * 70)
    
    precios_solo_numeros = []
    
    for i, art in enumerate(articulos_validos[:10], 1):
        print(f"{i}. [${art['precio']:.2f}] - {art['titulo']} (Publicado en {art['moneda_original']})")
        precios_solo_numeros.append(art['precio'])
        
    # ── Mini Análisis de Ruido ──
    if precios_solo_numeros:
        promedio_crudo = sum(precios_solo_numeros) / len(precios_solo_numeros)
        print("-" * 70)
        print(f"📈 Promedio Crudo: ${promedio_crudo:.2f}")

if __name__ == "__main__":
    print("🤖 BIENVENIDO AL ESPÍA DE PRUEBA DE MERCADO LIBRE")
    tasa = input("Ingresa la Tasa BCV de hoy (ej. 55.20) o presiona Enter para ignorar los VES: ")
    tasa_bcv = float(tasa) if tasa.strip() else None
    
    while True:
        query = input("\n📝 Ingresa un producto para buscar (o 'salir' para terminar): ")
        if query.lower() == 'salir':
            break
        buscar_en_mlv(query, tasa_bcv)