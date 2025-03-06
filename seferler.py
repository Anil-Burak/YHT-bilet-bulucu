from bs4 import BeautifulSoup
import multiprocessing
import sys, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from winreg import *


def scrape_yht(date, nereden, nereye):  # Çalışmıyor
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    with OpenKey(HKEY_CURRENT_USER,  # Varsayılan tarayıcı bulmak için (Windows için)
                 r"Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice") as key:
        browser = QueryValueEx(key, 'Progid')[0]
    if browser == "MSEdgeHTM":
        driver = webdriver.Edge(options=options)
    else:
        driver = webdriver.Chrome(options=options)
    try:
        driver.get("https://ebilet.tcddtasimacilik.gov.tr/")
        neredenButon = driver.find_element(By.ID, "fromTrainInput")
        neredenButon.click()
        neredenButon.send_keys(nereden)
        neredenSehir = driver.find_element(By.CLASS_NAME, "textLocation")
        neredenSehir.click()
        nereyeButon = driver.find_element(By.ID, "toTrainInput")
        nereyeButon.click()
        nereyeButon.send_keys(nereye)

        WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button.dropdown-item.station"))
        )

        # Bu yöntem çok mantıklı olmayabilir ama çalışıyor
        butonlar = driver.find_elements(By.CSS_SELECTOR, "button.dropdown-item.station")

        for buton in butonlar:
            if buton.is_displayed():
                buton.click()
                break

        driver.find_element(By.CSS_SELECTOR, 'div.datePickerInput').click()
        # TARİH
        tarih = driver.find_element(By.CSS_SELECTOR, f'td[data-date="{date}"]')
        driver.execute_script("arguments[0].click();", tarih)
        driver.find_element(By.ID, "searchSeferButton").click()  # Sefer ara

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "p.price"))
        )
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        seferler = []
        sefer_bloklari = soup.find_all('div', class_='seferInformation')

        for sefer in sefer_bloklari:
            tren_info = sefer.find('small')
            tren_adi = tren_info.get_text(strip=True) if tren_info else None

            saat_info = sefer.find('time', class_='text-danger')
            saatler = saat_info.get_text(strip=True) if saat_info else None

            sure_info = sefer.find('p')
            sure = sure_info.get_text(strip=True) if sure_info else 'Süre Bilinmiyor'

            if not tren_adi or not saatler or "EKSPRES" in tren_adi:
                continue

            vagonlar = []
            vagon_bloklari = sefer.find_all('button', class_='btnTicketType')

            if not vagon_bloklari:
                continue

            for vagon in vagon_bloklari:
                vagon_adi_tag = vagon.find('span', class_='mb-0 text-left')
                vagon_adi = vagon_adi_tag.get_text(strip=True) if vagon_adi_tag else 'Vagon Bilinmiyor'

                if vagon_adi == 'Vagon Bilinmiyor':
                    continue

                fiyat_tag = vagon.find('p', class_='price')
                fiyat = fiyat_tag.get_text(strip=True) if fiyat_tag else 'Fiyat Bilinmiyor'

                bos_koltuk_tag = vagon.find('span', class_='emptySeat')
                bos_koltuk = bos_koltuk_tag.get_text(strip=True) if bos_koltuk_tag else '0'
                bos_koltuk = bos_koltuk.strip("()")

                vagonlar.append({
                    'vagon_adi': vagon_adi,
                    'fiyat': fiyat,
                    'bos_koltuk': bos_koltuk
                })

            seferler.append({
                'tren_adi': tren_adi,
                'saatler': saatler,
                'sure': sure,
                'vagonlar': vagonlar
            })

        bos_ekonomi_var = any(
            any(vagon["vagon_adi"] == "EKONOMİ" and int(vagon["bos_koltuk"]) > 0 for vagon in sefer["vagonlar"])
            for sefer in seferler
        )

        sonuc = f"\n{'*' * 50}\n{date}\n"

        if not bos_ekonomi_var:
            sonuc += "Boş ekonomi koltuğu yok\n"
        else:
            for idx, sefer in enumerate(seferler, 1):
                if not any(vagon["vagon_adi"] == "EKONOMİ" and int(vagon["bos_koltuk"]) > 0 for vagon in
                           sefer["vagonlar"]):
                    continue

                sonuc += f"Sefer {idx}: {sefer['tren_adi']} {sefer['saatler']}\n"
                for vagon in sefer['vagonlar']:
                    sonuc += f"  - Vagon: {vagon['vagon_adi']}, Fiyat: {vagon['fiyat']}, Boş Koltuk: {vagon['bos_koltuk']}\n"
                sonuc += '-' * 40 + '\n'

        return sonuc

    except TimeoutException:
        return "Girilen verilerde hata var\n"
    finally:
        if driver:
            driver.quit()


def loading_animation(stop_event):
    while not stop_event.is_set():
        for dots in [".  ", ".. ", "..."]:
            sys.stdout.write(f"\rİşleminiz devam ediyor{dots}")
            sys.stdout.flush()
            time.sleep(0.5)


if __name__ == "__main__":
    dates = ["2025-03-05", "2025-03-06"]
    stop_event = multiprocessing.Event()
    anim_process = multiprocessing.Process(target=loading_animation, args=(stop_event,))
    nereden = "Ankara"
    nereye = "Pendik"
    args = [(date, nereden, nereye) for date in dates]
    anim_process.start()
    with multiprocessing.Pool(processes=4) as pool:
        results = pool.starmap(scrape_yht, args)
    stop_event.set()
    anim_process.join()
    # Sonuçları sırayla yazdır
    for result in results:
        print(result)
