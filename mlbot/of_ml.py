import requests
from bs4 import BeautifulSoup
import asyncio
from telegram import Bot
import random

# === CONFIGURACIÓN ===
TOKEN = "8378991301:AAGCPkLeOiZSalTjftV1PIWi3K6hpcT8Xa4"
CHAT_ID = "-1002524247794"
CATEGORIAS_VALIDAS = [
    "audifonos", "celulares", "cargadores", "ropa-hombre", "zapatos",
    "accesorios-para-autos", "hogar", "relojes", "luces-led", "gimnasio"
]
NUM_OFERTAS = 1

bot = Bot(token=TOKEN)

async def extraer_info_producto(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            return {
                "titulo": "Error al cargar",
                "precio": "N/A",
                "precio_anterior": None,
                "descuento": None,
                "link": url
            }
        
        soup = BeautifulSoup(resp.text, "lxml")

        titulo = soup.find("h1", class_="ui-pdp-title")
        titulo = titulo.get_text(strip=True) if titulo else "Sin título"

        precio_container = soup.find("div", class_="ui-pdp-price__second-line")

        precio = "Sin precio"
        precio_anterior = None
        descuento = None

        if precio_container:
            anterior_tag = precio_container.find("s", class_="andes-money-amount")
            if anterior_tag:
                anterior_fraction = anterior_tag.find("span", class_="andes-money-amount__fraction")
                if anterior_fraction:
                    precio_anterior = anterior_fraction.get_text(strip=True)

            actual_tag = precio_container.find_all("span", class_="andes-money-amount__fraction")
            if actual_tag:
                precio = actual_tag[-1].get_text(strip=True)

        descuento_tag = soup.find("span", class_=lambda x: x and "andes-money-amount__discount" in x)
        if descuento_tag:
            descuento = descuento_tag.get_text(strip=True)

        print(f"DEBUG: {titulo} | Actual: {precio} | Anterior: {precio_anterior} | Descuento: {descuento}")

        return {
            "titulo": titulo,
            "precio": precio,
            "precio_anterior": precio_anterior,
            "descuento": descuento,
            "link": url
        }

    except Exception as e:
        return {
            "titulo": "Error",
            "precio": str(e),
            "precio_anterior": None,
            "descuento": None,
            "link": url
        }

async def obtener_ofertas(termino_busqueda, maximo=1):
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://listado.mercadolibre.com.mx/{termino_busqueda.replace(' ', '-')}"
    resp = requests.get(url, headers=headers)

    if resp.status_code != 200:
        print("❌ No se pudo acceder al listado.")
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    items = soup.find_all("li", class_="ui-search-layout__item")

    enlaces = []
    for item in items:
        a_tag = item.find("a", href=True)
        if a_tag and "mercadolibre.com.mx" in a_tag["href"]:
            enlaces.append(a_tag["href"])
        if len(enlaces) >= maximo:
            break

    ofertas = []
    for enlace in enlaces:
        datos = await extraer_info_producto(enlace)
        ofertas.append(datos)
        await asyncio.sleep(1)

    return ofertas

async def mandar_a_telegram(ofertas):
    for o in ofertas:
        if o["precio_anterior"]:
            if o["descuento"]:
                mensaje = (
                    f"🎧 {o['titulo']}\n"
                    f"~${o['precio_anterior']}~ → ${o['precio']} "
                    f"({o['descuento']})\n"
                    f"🔗 [Ver oferta]({o['link']})"
                )
            else:
                mensaje = (
                    f"🎧 {o['titulo']}\n"
                    f"~${o['precio_anterior']}~ → ${o['precio']}\n"
                    f"🔗 [Ver oferta]({o['link']})"
                )
        elif o["descuento"]:
            mensaje = (
                f"🎧 {o['titulo']}\n"
                f"${o['precio']} ({o['descuento']})\n"
                f"🔗 [Ver oferta]({o['link']})"
            )
        else:
            mensaje = f"🎧 {o['titulo']} a solo ${o['precio']}\n🔗 [Ver oferta]({o['link']})"

        try:
            await bot.send_message(chat_id=CHAT_ID, text=mensaje, parse_mode='Markdown')
            print(f"✅ Mensaje enviado: {o['titulo']}")
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {e}")

async def loop_automatico():
    categoria = random.choice(CATEGORIAS_VALIDAS)
    print(f"🔄 Buscando ofertas en: {categoria}")
    ofertas = await obtener_ofertas(categoria, NUM_OFERTAS)
    if ofertas:
        await mandar_a_telegram(ofertas)
    else:
        print(f"⚠️ No se encontraron ofertas para: {categoria}")

if __name__ == "__main__":
    asyncio.run(loop_automatico())

