#!/bin/bash

# Questo script assume che la variabile d'ambiente ENV_NAME sia impostata
# nel tuo Dockerfile (es. ENV ENV_NAME=dicomseg).
# Se lo script viene eseguito all'interno del container Docker, ENV_NAME dovrebbe essere disponibile.
# In caso contrario, puoi sostituire "$ENV_NAME" con "dicomseg" direttamente.
CONDA_ENV_NAME="${ENV_NAME:-dicomseg}"

# Funzione per stampare messaggi di errore ed uscire
error_exit() {
    echo ""
    echo "ERRORE: $1" >&2
    exit 1
}

echo "Working with :"
echo "1) rtstruct "
echo "2) nifti - dicom"
echo ""
read -r -p "Insert your choise : " choice
echo ""

case $choice in
    1)
        echo "rtstruct."
        echo "--------------------------------------------------"

        # Si presume che 'rtstruct2dcmseg' sia un comando reso disponibile nel PATH
        # dallo script /usr/rtstruct/install_enviorment.sh.
        # Se 'rtstruct2dcmseg' è in realtà uno script Python (es. /usr/rtstruct/rtstruct2dcmseg.py),
        # la chiamata dovrebbe essere:
        # conda run -n "$CONDA_ENV_NAME" python /usr/rtstruct/rtstruct2dcmseg.py "$@"
        #
        # Verifica il nome e il percorso corretto dello script/comando installato da install_enviorment.sh.
        if command -v rtstruct2dcmseg.py &> /dev/null; then
            conda run -n "$CONDA_ENV_NAME" rtstruct2dcmseg.py "$@"
        else
            # Forniamo un messaggio di errore più dettagliato se il comando non viene trovato.
            # Potrebbe essere necessario che l'utente verifichi l'output di install_enviorment.sh
            # o il contenuto della directory /usr/rtstruct.
            error_exit "Comando 'rtstruct2dcmseg.py' non trovato.
Possibili cause:
1. 'rtstruct2dcmseg' non è stato installato correttamente da '/usr/rtstruct/install_enviorment.sh'.
2. Non è nel PATH dell'ambiente Conda '$CONDA_ENV_NAME'.
3. Potrebbe avere un nome diverso o richiedere di essere chiamato con 'python /percorso/allo/script.py'.
Verifica l'installazione e la configurazione di rtstruct."
        fi
        ;;
    2)
        echo "Hai scelto: altro."
        echo "Tentativo di esecuzione di 'dicom_conversion.py' (come /usr/dcmqi/bin/dcm2nifti.py)..."
        echo "--------------------------------------------------"

        # Dal Dockerfile: COPY dicom_conversion.py /usr/dcmqi/bin/dcm2nifti.py
        SCRIPT_PATH="/usr/dcmqi/bin/dcm2nifti.py"

        if [ -f "$SCRIPT_PATH" ]; then
            conda run -n "$CONDA_ENV_NAME" python "$SCRIPT_PATH" "$@"
        else
            error_exit "Script '$SCRIPT_PATH' non trovato. Verifica che il Dockerfile lo copi correttamente."
        fi
        ;;
    *)
        error_exit "Scelta non valida: '$choice'. Inserisci 1 o 2."
        ;;
esac

# Cattura lo stato di uscita dello script eseguito
exit_status=$?

if [ $exit_status -ne 0 ]; then
    echo "--------------------------------------------------"
    echo "ATTENZIONE: Lo script selezionato è terminato con un errore (codice di uscita: $exit_status)."
fi

exit $exit_status
