import re
import sys, time
from seferler import scrape_yht
from bilet import bilet_al
import multiprocessing

tarih_gecerlilik = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$"
bilet_gecerlilik = r"^(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01]) (0[0-9]|1[0-9]|2[0-3]):([0-5][0-9])$"


def loading_animation(stop_event):
    while not stop_event.is_set():
        for dots in [".  ", ".. ", "..."]:
            sys.stdout.write(f"\rİşleminiz devam ediyor{dots}")
            sys.stdout.flush()
            time.sleep(0.5)


def control():
    nereden = input("Hangi istasyondan: ")
    nereye = input("Hangi istasyona: ")
    dates = []
    print("Taramak istediğiniz tarihler 'aa-gg' şeklinde olmalıdır.")
    print("Örneğin: 06-27")
    while True:
        girdiTarih = input("Tarihleri giriniz: ")
        if girdiTarih == "e":
            break
        if re.match(tarih_gecerlilik, girdiTarih):
            girdiTarih = "2025-" + girdiTarih
            dates.append(girdiTarih)
            print("Tarih eklendi. Eklemeye devam edebilir veya taramaya başlamak için 'e' girebilirsiniz.")
        else:
            print("Doğru formatta girmediniz")
    args = [(date, nereden, nereye) for date in dates]
    stop_event = multiprocessing.Event()
    anim_process = multiprocessing.Process(target=loading_animation, args=(stop_event,))
    anim_process.start()
    with multiprocessing.Pool(processes=4) as pool:  # 4'ten fazla browser çok yavaşlatıyor
        results = pool.starmap(scrape_yht, args)
    stop_event.set()
    anim_process.join()
    for result in results:
        print(result)
    print("\n\033[3mBilet ekranına gitmek için istediğiniz tarih ve saati girebilirsiniz.\033[0m")
    print("\033[3mGirdi 'gg-aa' 'ss:dd' şeklinde olmalıdır. Örn: 06-27 08:05\033[0m")
    while True:
        biletGirdi = input("\033[1mBilet tarih ve saatini girin: \033[0m")
        if re.match(bilet_gecerlilik, biletGirdi):
            print("Bilet sayfası açılıyor...")
            biletVeriler = biletGirdi.split(' ')
            break
        else:
            print("Girilen verilerde hata var")
    bilet_al(nereden, nereye, biletVeriler[0], biletVeriler[1])
    return
