#!/bin/bash
# Ollama Model Cleanup
# Usage: ./ollama_cleanup.sh [--all] [--old DAYS] [--dry-run]

DRY_RUN=false
REMOVE_ALL=false
OLD_DAYS=0

for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --all)     REMOVE_ALL=true ;;
        --old)     shift; OLD_DAYS="${1:-90}" ;;
    esac
done

if ! command -v ollama &>/dev/null; then
    echo "ollama not found. Install via: brew install ollama"
    exit 1
fi

echo "=== Ollama Models ==="
ollama list
echo ""

# Calculate total size
TOTAL=$(ollama list | tail -n +2 | awk '{print $3, $4}' | awk '
    /GB/ { sum += $1 }
    /MB/ { sum += $1/1024 }
    END  { printf "%.1f GB\n", sum }
')
MODEL_COUNT=$(ollama list | tail -n +2 | wc -l | tr -d ' ')
echo "Total: $MODEL_COUNT models, ~$TOTAL"
echo ""

# --all flag: remove everything
if $REMOVE_ALL; then
    echo "Removing ALL models..."
    ollama list | tail -n +2 | awk '{print $1}' | while read -r model; do
        echo "  Removing $model..."
        $DRY_RUN || ollama rm "$model"
    done
    echo "Done."
    exit 0
fi

# Interactive mode
echo "Options:"
echo "  [a] Remove all models"
echo "  [s] Select models to remove interactively"
echo "  [o] Remove models not used in 90+ days"
echo "  [q] Quit"
echo ""
read -rp "Choice: " choice

case $choice in
    a|A)
        read -rp "Remove ALL $MODEL_COUNT models (~$TOTAL)? (y/N) " confirm
        [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
        ollama list | tail -n +2 | awk '{print $1}' | while read -r model; do
            echo "  Removing $model..."
            $DRY_RUN || ollama rm "$model"
        done
        ;;

    s|S)
        echo ""
        echo "Enter model names to remove (space-separated), or press Enter to cancel:"
        ollama list | tail -n +2 | awk '{printf "  %-40s %s %s\n", $1, $3, $4}'
        echo ""
        read -rp "Models to remove: " -a selected
        if [[ ${#selected[@]} -eq 0 ]]; then
            echo "Nothing selected."
            exit 0
        fi
        echo ""
        for model in "${selected[@]}"; do
            echo "  Removing $model..."
            $DRY_RUN || ollama rm "$model" 2>&1
        done
        ;;

    o|O)
        echo ""
        echo "Models last used 90+ days ago:"
        ollama list | tail -n +2 | while read -r line; do
            model=$(echo "$line" | awk '{print $1}')
            modified=$(echo "$line" | awk '{print $5, $6, $7}')
            # Check if "months ago" or "year" appears
            if echo "$modified" | grep -qE "[3-9]+ months|[0-9]+ year"; then
                size=$(echo "$line" | awk '{print $3, $4}')
                echo "  $model ($size) — $modified"
            fi
        done
        echo ""
        read -rp "Remove these models? (y/N) " confirm
        [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
        ollama list | tail -n +2 | while read -r line; do
            model=$(echo "$line" | awk '{print $1}')
            modified=$(echo "$line" | awk '{print $5, $6, $7}')
            if echo "$modified" | grep -qE "[3-9]+ months|[0-9]+ year"; then
                echo "  Removing $model..."
                $DRY_RUN || ollama rm "$model"
            fi
        done
        ;;

    q|Q|"")
        echo "Exiting."
        exit 0
        ;;

    *)
        echo "Invalid choice."
        exit 1
        ;;
esac

echo ""
echo "=== Remaining models ==="
ollama list
echo ""
echo "=== Disk status ==="
df -h /
