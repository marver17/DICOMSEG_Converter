# Test Suite - DicomConverter

Questa cartella contiene la suite completa di test per il container DicomConverter.

## 📂 Contenuto

```
tests/
├── README.md                        # Questo file
├── quick_test.sh                    # ⚡ Test rapido: build + test in un comando
├── run_container_tests.sh           # 🧪 Suite completa con 9 test
├── test_container_validation.py     # ✓ Validazione automatica degli output
├── TESTING_GUIDE.md                 # 📖 Guida completa e dettagliata
├── TESTING_README.md                # 📄 Riferimento rapido
└── test_output/                     # 📁 Output dei test (creata automaticamente)
    ├── test_log_*.txt               # Log dei test con timestamp
    └── test*/                       # Output di ciascun test
```

## 🚀 Quick Start

### Opzione 1: Test Rapido (Consigliato per Prima Esecuzione)

```bash
cd tests
./quick_test.sh
```

Questo comando esegue automaticamente:
1. **Build** del container Docker dalla directory principale
2. **Test** di tutte le funzionalità (9 test)
3. **Validazione** degli output generati
4. **Report** finale con sommario

**Tempo stimato**: 5-10 minuti (include build)

### Opzione 2: Solo Test (Container già buildato)

```bash
cd tests
./run_container_tests.sh [nome_immagine]
```

Se non specifichi il nome dell'immagine, usa `dicomconverter:latest` di default.

**Tempo stimato**: 2-3 minuti

### Opzione 3: Solo Validazione Output

```bash
cd tests
python test_container_validation.py test_output
```

Valida gli output di test già eseguiti.

## 📋 Test Eseguiti

La suite include **9 test** che coprono tutte le funzionalità:

### 1. Test Basici (2 test)
- **Test 1**: Verifica help command
- **Test 2**: Verifica versione conda

### 2. Conversioni RT-STRUCT → DICOM SEG (4 test)
- **Test 3**: LUNG1-001 (CT scan con RT-STRUCT)
- **Test 4**: interobs05 (CT con multiple strutture)
- **Test 5**: AMBL-001 (MR breast con segmentazione)
- **Test 6**: Pedro's multi-modality (US/MR/CT con registration)

### 3. Conversioni DICOM SEG → NIfTI (1 test)
- **Test 7**: Estrazione segmentazione da DICOM SEG

### 4. Modulo di Validazione (1 test)
- **Test 8**: Validazione geometrica (4 controlli)

### 5. Batch Processing (1 test)
- **Test 9**: Elaborazione batch con CSV

## 📊 Output e Log

### Struttura Output

Dopo l'esecuzione, troverai:

```
test_output/
├── test_log_20231103_143025.txt    # Log completo con timestamp
├── test1_help.txt                  # Output test 1
├── test2_conda.txt                 # Output test 2
├── test3_lung1_seg.dcm             # Segmentazione test 3
├── test4_interobs_seg.dcm          # Segmentazione test 4
├── test5_ambl001_seg.dcm           # Segmentazione test 5
├── test6_pedro_mr_seg.dcm          # Segmentazione test 6 (MR)
├── test6_pedro_us_seg.dcm          # Segmentazione test 6 (US)
├── test7_extracted/                # NIfTI estratti test 7
├── test8_validation.txt            # Output validazione test 8
└── test9_batch_log.txt             # Log batch test 9
```

### Interpretare i Log

I file di log contengono:
- **Timestamp** di inizio/fine per ogni test
- **Comando** Docker eseguito
- **Output** completo (stdout + stderr)
- **Status**: PASSED o FAILED
- **Sommario** finale con statistiche

Esempio log:
```
----------------------------------------
TEST 3: RT-STRUCT to DICOM SEG - LUNG1-001
Command: docker run --rm -v /path/to/DATA:/data ...
Started: Sun Nov  3 14:30:25 2024
...
Status: PASSED
Ended: Sun Nov  3 14:30:28 2024
```

## 🔍 Validazione Output

### Validazione Automatica

```bash
python test_container_validation.py test_output
```

Questo script verifica:
- ✓ Esistenza file output
- ✓ Validità DICOM (header, tag richiesti)
- ✓ Dimensioni file (> 0 bytes)
- ✓ Formato DICOM SEG corretto
- ✓ Presenza SOP Class UID

### Validazione Manuale

Per verificare manualmente un file DICOM:

```bash
# Con pydicom
python3 -c "import pydicom; ds=pydicom.dcmread('test_output/test3_lung1_seg.dcm'); print(ds)"

# Con dcmdump (se disponibile)
dcmdump test_output/test3_lung1_seg.dcm
```

## 🛠️ Troubleshooting

### Test Falliscono

1. **Verifica Docker in esecuzione**:
   ```bash
   docker ps
   ```

2. **Controlla il log dettagliato**:
   ```bash
   cat test_output/test_log_*.txt
   ```

3. **Verifica i dati di input**:
   ```bash
   ls -lah ../DATA/EucaimShared/Test1/LUNG1-001/
   ```

4. **Test singolo in debug**:
   ```bash
   docker run --rm -v $(pwd)/../DATA:/data dicomconverter:latest rtstruct2seg --help
   ```

### Container non si builda

1. **Pulisci build precedenti**:
   ```bash
   docker system prune -a
   ```

2. **Build con output dettagliato**:
   ```bash
   cd ..
   docker build -t dicomconverter:latest . 2>&1 | tee build.log
   ```

3. **Verifica spazio disco**:
   ```bash
   df -h
   ```

### Output non valido

1. **Verifica presenza file**:
   ```bash
   ls -lh test_output/
   ```

2. **Controlla permessi**:
   ```bash
   ls -la test_output/
   ```

3. **Valida DICOM manualmente**:
   ```bash
   python3 test_container_validation.py test_output --verbose
   ```

## 📖 Documentazione Completa

Per informazioni dettagliate su ogni test, consulta:

- **`TESTING_GUIDE.md`**: Guida completa con esempi e spiegazioni
- **`TESTING_README.md`**: Riferimento rapido dei comandi
- **`../examples/VALIDATION_GUIDE.md`**: Guida alla validazione geometrica
- **`../examples/BATCH_GUIDE.md`**: Guida al batch processing

## 🔄 Workflow Consigliato

### Per Sviluppo

1. Modifica il codice in `../src/`
2. Esegui test rapido: `./quick_test.sh`
3. Verifica log: `cat test_output/test_log_*.txt`
4. Itera fino a successo

### Per CI/CD

```bash
#!/bin/bash
cd tests
./quick_test.sh
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo "All tests passed!"
    # Tag and push image
    docker tag dicomconverter:latest myregistry/dicomconverter:latest
    docker push myregistry/dicomconverter:latest
else
    echo "Tests failed with code $exit_code"
    exit 1
fi
```

### Per Produzione

Prima di deployare:

1. **Test completo**: `./quick_test.sh`
2. **Validazione manuale** di almeno 2 output
3. **Test su dati reali** del tuo dataset
4. **Verifica log** per warning/error

## 📝 Aggiungere Nuovi Test

Per aggiungere un test alla suite:

1. Apri `run_container_tests.sh`
2. Copia un test esistente come template
3. Modifica:
   - Nome test
   - Comando Docker
   - Path output atteso
4. Incrementa il numero test
5. Esegui per verificare

Esempio:
```bash
# Test 10: New conversion test
run_test "New conversion test" \
    "docker run --rm -v \"$DATA_DIR\":/data -v \"$OUTPUT_DIR\":/output \
    $DOCKER_IMAGE new_mode -i /data/input -o /output/test10_output.dcm" \
    "$OUTPUT_DIR/test10_output.dcm"
```

## 🤝 Contribuire

Per migliorare i test:

1. **Aggiungi casi edge**: Dati particolari, dimensioni estreme
2. **Migliora validazione**: Più controlli in `test_container_validation.py`
3. **Documenta**: Aggiorna `TESTING_GUIDE.md`
4. **Benchmark**: Misura tempi di esecuzione

## 📊 Metriche Test

Dopo ogni esecuzione, il report finale mostra:

```
=====================================
Test Summary
=====================================
Total Tests: 9
Passed: 9
Failed: 0
Success Rate: 100%
Total Time: 3m 42s
=====================================
```

---

**Ultimo aggiornamento**: Novembre 2025

Per eseguire i test ora:
```bash
./quick_test.sh
```
