#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIOS_DIR="${SCENARIOS_DIR:-${SCRIPT_DIR}/scenarios}"

usage() {
  cat <<'EOF'
Usage: ./scripts/runscenario.sh [scenario] [--yes] [--pause-seconds N]

Lists scenarios discovered under scripts/scenarios and runs the selected one.

Options:
  scenario              Optional scenario directory name, e.g. valid-order
  -y, --yes             Forward to the scenario runner to skip prompts
  --pause-seconds N     Forward to the scenario runner
  -h, --help            Show this help

Examples:
  ./scripts/runscenario.sh
  ./scripts/runscenario.sh --yes
  ./scripts/runscenario.sh valid-order --yes
EOF
}

scenario_names=()
while IFS= read -r run_script; do
  scenario_names+=("$(basename "$(dirname "$run_script")")")
done < <(find "$SCENARIOS_DIR" -mindepth 2 -maxdepth 2 -type f -name run.sh | sort)

if [ "${#scenario_names[@]}" -eq 0 ]; then
  echo "No scenarios found under ${SCENARIOS_DIR}."
  echo "Add a subdirectory with a run.sh file, then try again."
  exit 1
fi

selected=""
scenario_args=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    -y|--yes)
      scenario_args+=("$1")
      shift
      ;;
    --pause-seconds)
      if [ "$#" -lt 2 ]; then
        echo "--pause-seconds requires a value."
        exit 1
      fi
      scenario_args+=("$1" "$2")
      shift 2
      ;;
    --)
      shift
      while [ "$#" -gt 0 ]; do
        scenario_args+=("$1")
        shift
      done
      ;;
    *)
      if [ -z "$selected" ] && [ -f "${SCENARIOS_DIR}/$1/run.sh" ]; then
        selected="$1"
      else
        scenario_args+=("$1")
      fi
      shift
      ;;
  esac
done

print_scenarios() {
  echo "Available scenarios:"
  local i
  for i in "${!scenario_names[@]}"; do
    printf "  %2d) %s\n" "$((i + 1))" "${scenario_names[$i]}"
  done
}

choose_scenario() {
  local choice
  while true; do
    print_scenarios
    echo ""
    read -r -p "Select a scenario by number or name (q to quit): " choice

    case "$choice" in
      q|Q|quit|exit)
        exit 0
        ;;
      '' )
        echo "Please enter a scenario number or name."
        echo ""
        ;;
      * )
        if [[ "$choice" =~ ^[0-9]+$ ]]; then
          if [ "$choice" -ge 1 ] && [ "$choice" -le "${#scenario_names[@]}" ]; then
            selected="${scenario_names[$((choice - 1))]}"
            return
          fi
        else
          local name
          for name in "${scenario_names[@]}"; do
            if [ "$choice" = "$name" ]; then
              selected="$name"
              return
            fi
          done
        fi
        echo "Unknown scenario: ${choice}"
        echo ""
        ;;
    esac
  done
}

if [ -z "$selected" ]; then
  choose_scenario
fi

run_script="${SCENARIOS_DIR}/${selected}/run.sh"
if [ ! -f "$run_script" ]; then
  echo "Scenario '${selected}' does not have a run.sh file."
  exit 1
fi

echo "Running scenario: ${selected}"
echo ""
exec /bin/bash "$run_script" "${scenario_args[@]}"
