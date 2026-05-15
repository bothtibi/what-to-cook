# Ajánló algoritmus

Ez a dokumentum a jelenlegi receptajánló működését írja le. A cél, hogy a pontozást külön, átláthatóan tudjuk finomítani.

## Fájlok

- `src/recommendation_algorithm.py`: a tényleges pontozási és szűrési logika.
- `src/recommendations.py`: receptek lekérése, pontozott lista rendezése, leves + főétel kombinációk összeállítása.
- `src/ui/recommendation_page.py`: UI paraméterek, például darabszám és max elkészítési idő.

## Bemenetek

Egy recept pontozásánál az algoritmus ezeket használja:

- recept kategória,
- tagek,
- elkészítési idő percben,
- Tibi / Melinda kedvenc jelölések,
- Tibi / Melinda nem szereti jelölések,
- archivált állapot,
- utolsó főzés dátuma,
- eddigi főzések száma.

## Kemény Szűrések

Ezek a receptek nem kerülnek ajánlásba:

- archivált recept,
- amit Tibi és Melinda is nem szeret,
- ami túllépi a UI-ban megadott max elkészítési időt.

Megjegyzés: ha egy recept elkészítési ideje `0`, az jelenleg “ismeretlen idő”-nek számít, ezért nem esik ki a max idő szűrésen.

## Pontozás

Minden recept `10.0` alappontról indul.

Jelenlegi pozitív hatások:

- kedvenc jelölés személyenként: `+2.0`,
- `gyors` tag: `+1.1`,
- `kedvenc` tag: `+1.0`,
- `klasszikus` tag: `+0.7`,
- `sütőben` tag: `+0.4`,
- `kiadós` tag: `+0.4`,
- elkészítési idő legfeljebb 30 perc: `+0.8`,
- ha még nincs historyban: `+3.0`,
- régen főzött étel fokozatos boostot kap, legfeljebb `+8.0`.

Jelenlegi negatív hatások:

- ha valaki nem szereti: `-4.0`,
- 90 perc vagy hosszabb elkészítési idő: `-0.8`,
- ha 3 napon belül volt főzve: `-8.0`,
- ha 7 napon belül volt főzve: `-3.5`,
- gyakori főzés büntetése: főzések száma alapján, legfeljebb `-6.0`.

Van egy kis véletlen faktor is: `-0.35` és `+0.35` között. Ez arra szolgál, hogy az azonos pontszámú vagy nagyon hasonló receptek ne mindig ugyanabban a sorrendben jelenjenek meg.

## Kombinációk

A leves + főétel ajánlás külön pontozza a leveseket és a főételeket. Ezután minden lehetséges leves-főétel párt összeállít, és a kombináció pontszáma:

```text
(leves pontszám + főétel pontszám) / 2
```

Ezután a rendszer pontszám szerint rendezi a kombinációkat, és a kért darabszámig ad vissza találatokat.

## Finomítási Ötletek

1. Mennyire büntessük azt, amit csak egyikőtök nem szeret?
2. A kedvenc jelölés legyen-e erősebb, mint a régen főzött hatás?
3. Legyen-e külön hétköznapi és hétvégi ajánlási logika?
4. A leves + főétel kombináció figyelje-e az összesített elkészítési időt?
5. Legyenek-e szezonális tagek, például nyári, téli, ünnepi?
6. A túl gyakran főzött kedvenceket mennyire fogjuk vissza?
