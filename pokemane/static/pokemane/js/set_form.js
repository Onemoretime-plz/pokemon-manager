function clearOptions(selectElement) {
    while (selectElement.firstChild) {
        selectElement.removeChild(selectElement.firstChild);
    }
}

function addOption(selectElement, value, label, selected = false) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = label;

    if (selected) {
        option.selected = true;
    }

    selectElement.appendChild(option);
}

function updateAbilityOptions() {
    const pokemonSelect = document.getElementById("pokemon-select");
    const abilitySelect = document.getElementById("ability-select");

    if (!pokemonSelect || !abilitySelect) {
        return;
    }

    const pokemonId = pokemonSelect.value;
    const abilityMap = window.POKEMANE_POKEMON_ABILITIES || {};
    const abilities = abilityMap[pokemonId] || [];

    const currentAbility = abilitySelect.dataset.currentAbility || "";

    clearOptions(abilitySelect);

    if (!pokemonId) {
        addOption(abilitySelect, "", "ポケモンを選択してください", true);
        return;
    }

    if (abilities.length === 0) {
        addOption(abilitySelect, "", "登録特性なし", true);
        return;
    }

    abilities.forEach((ability, index) => {
        const selected = currentAbility
            ? ability === currentAbility
            : index === 0;

        addOption(abilitySelect, ability, ability, selected);
    });
}

function updateMegaOptions() {
    const pokemonSelect = document.getElementById("pokemon-select");
    const megaCheckbox = document.getElementById("mega-stone-checkbox");
    const megaSelect = document.getElementById("mega-evolution-select");
    const megaField = document.getElementById("mega-evolution-field");
    const megaHelp = document.getElementById("mega-evolution-help");

    if (!pokemonSelect || !megaCheckbox || !megaSelect) {
        return;
    }

    const pokemonId = pokemonSelect.value;
    const megaMap = window.POKEMANE_POKEMON_MEGAS || {};
    const megaOptions = megaMap[pokemonId] || [];
    const currentMega = megaSelect.dataset.currentMega || "";

    clearOptions(megaSelect);
    addOption(megaSelect, "", "なし", true);

    if (!pokemonId || megaOptions.length === 0) {
        megaCheckbox.checked = false;
        megaCheckbox.disabled = true;
        megaSelect.disabled = true;

        if (megaField) {
            megaField.classList.add("disabled-field");
        }

        if (megaHelp) {
            megaHelp.textContent = "このポケモンには登録済みのメガ進化先がありません。";
        }

        return;
    }

    megaCheckbox.disabled = false;

    if (megaField) {
        megaField.classList.remove("disabled-field");
    }

    megaOptions.forEach((mega) => {
        const selected = currentMega
            ? String(mega.id) === String(currentMega)
            : false;

        addOption(megaSelect, String(mega.id), mega.label, selected);
    });

    if (!megaCheckbox.checked) {
        megaSelect.disabled = true;

        if (megaHelp) {
            megaHelp.textContent = "メガストーンをONにすると選択されます。";
        }

        return;
    }

    megaSelect.disabled = false;

    if (megaOptions.length === 1) {
        megaSelect.value = String(megaOptions[0].id);
        megaSelect.disabled = true;

        if (megaHelp) {
            megaHelp.textContent = "メガ進化先が1つのため自動選択されています。";
        }

        return;
    }

    if (currentMega) {
        megaSelect.value = currentMega;
    } else {
        megaSelect.value = String(megaOptions[0].id);
    }

    if (megaHelp) {
        megaHelp.textContent = "メガ進化先が複数あるため、使用するメガ進化先を選択してください。";
    }
}

function handlePokemonChange() {
    const abilitySelect = document.getElementById("ability-select");
    const megaSelect = document.getElementById("mega-evolution-select");

    if (abilitySelect) {
        abilitySelect.dataset.currentAbility = "";
    }

    if (megaSelect) {
        megaSelect.dataset.currentMega = "";
    }

    updateAbilityOptions();
    updateMegaOptions();
}

function updatePokemonIconPreview(selectElement) {
    const iconTargetId = selectElement.dataset.iconTarget;

    if (!iconTargetId) {
        return;
    }

    const iconElement = document.getElementById(iconTargetId);

    if (!iconElement) {
        return;
    }

    const iconBox = iconElement.closest(".selected-pokemon-icon-box");
    const placeholder = iconBox
        ? iconBox.querySelector(".selected-pokemon-icon-placeholder")
        : null;

    const pokemonId = selectElement.value;
    const iconMap = window.POKEMANE_POKEMON_ICONS || {};
    const pokemonData = iconMap[pokemonId];

    if (!pokemonId) {
        iconElement.classList.add("hidden");
        iconElement.removeAttribute("src");
        iconElement.alt = "";

        if (placeholder) {
            placeholder.classList.add("hidden");
        }

        return;
    }

    if (!pokemonData || !pokemonData.icon_url) {
        iconElement.classList.add("hidden");
        iconElement.removeAttribute("src");
        iconElement.alt = "";

        if (placeholder) {
            placeholder.classList.remove("hidden");
        }

        return;
    }

    iconElement.src = pokemonData.icon_url;
    iconElement.alt = pokemonData.name;
    iconElement.classList.remove("hidden");

    if (placeholder) {
        placeholder.classList.add("hidden");
    }
}

function attachPokemonIconPreview(selectElement) {
    updatePokemonIconPreview(selectElement);

    selectElement.addEventListener("change", () => {
        updatePokemonIconPreview(selectElement);
    });
}

function initializePokemonIconPreviews() {
    const selects = document.querySelectorAll(".pokemon-icon-select");

    selects.forEach((selectElement) => {
        attachPokemonIconPreview(selectElement);
    });
}

function filterPokemonSelectOptions(inputElement) {
    const targetSelectId = inputElement.dataset.filterTarget;

    if (!targetSelectId) {
        return;
    }

    const selectElement = document.getElementById(targetSelectId);

    if (!selectElement) {
        return;
    }

    const keyword = inputElement.value.trim().toLowerCase();
    const options = selectElement.querySelectorAll("option");

    options.forEach((option) => {
        if (!option.value) {
            option.hidden = false;
            return;
        }

        const searchText = (option.dataset.searchText || option.textContent || "").toLowerCase();

        if (!keyword || searchText.includes(keyword)) {
            option.hidden = false;
        } else {
            option.hidden = true;
        }
    });

    const selectedOption = selectElement.options[selectElement.selectedIndex];

    if (selectedOption && selectedOption.hidden) {
        selectElement.value = "";
        updatePokemonIconPreview(selectElement);
    }
}

function attachPokemonSelectFilter(inputElement) {
    inputElement.addEventListener("input", () => {
        filterPokemonSelectOptions(inputElement);
    });
}

function initializePokemonSelectFilters() {
    const filterInputs = document.querySelectorAll(".pokemon-option-filter");

    filterInputs.forEach((inputElement) => {
        attachPokemonSelectFilter(inputElement);
    });
}

function addDynamicRow(templateId, gridId, countInputId) {
    const template = document.getElementById(templateId);
    const grid = document.getElementById(gridId);
    const countInput = document.getElementById(countInputId);

    if (!template || !grid || !countInput) {
        return;
    }

    const nextNumber = Number(countInput.value || 0) + 1;
    countInput.value = String(nextNumber);

    const html = template.innerHTML.replaceAll("__number__", String(nextNumber));

    const wrapper = document.createElement("div");
    wrapper.innerHTML = html.trim();

    const newRow = wrapper.firstElementChild;
    grid.appendChild(newRow);

    const select = newRow.querySelector(".pokemon-icon-select");

    if (select) {
        attachPokemonIconPreview(select);
    }

    const filterInput = newRow.querySelector(".pokemon-option-filter");

    if (filterInput) {
        attachPokemonSelectFilter(filterInput);
    }

    if (gridId === "matchup-form-grid") {
        renumberDynamicRows("matchup");
    }

    if (gridId === "weak-matchup-form-grid") {
        renumberDynamicRows("weak");
    }
}


function updateRowAttributes(row, rowType, number) {
    const isMatchup = rowType === "matchup";
    const labelPrefix = isMatchup ? "役割" : "苦手";
    const targetNamePrefix = isMatchup ? "matchup_target" : "weak_target";
    const memoNamePrefix = isMatchup ? "matchup_memo" : "weak_memo";
    const iconPrefix = isMatchup ? "matchup-icon" : "weak-icon";
    const selectPrefix = isMatchup ? "matchup-select" : "weak-select";

    const numberElement = row.querySelector(".matchup-number");
    if (numberElement) {
        numberElement.textContent = `${labelPrefix}${number}`;
    }

    const targetSelect = row.querySelector(".pokemon-icon-select");
    if (targetSelect) {
        targetSelect.name = `${targetNamePrefix}_${number}`;
        targetSelect.id = `${selectPrefix}-${number}`;
        targetSelect.dataset.iconTarget = `${iconPrefix}-${number}`;
    }

    const filterInput = row.querySelector(".pokemon-option-filter");
    if (filterInput) {
        filterInput.dataset.filterTarget = `${selectPrefix}-${number}`;
    }

    const iconElement = row.querySelector(".selected-pokemon-icon");
    if (iconElement) {
        iconElement.id = `${iconPrefix}-${number}`;
    }

    const memoInput = row.querySelector(`input[name^="${memoNamePrefix}_"]`);
    if (memoInput) {
        memoInput.name = `${memoNamePrefix}_${number}`;
    }

    if (isMatchup) {
        const methodSelect = row.querySelector('select[name^="matchup_method_"]');
        if (methodSelect) {
            methodSelect.name = `matchup_method_${number}`;
        }
    }
}

function renumberDynamicRows(rowType) {
    const gridId = rowType === "matchup"
        ? "matchup-form-grid"
        : "weak-matchup-form-grid";

    const countInputId = rowType === "matchup"
        ? "matchup-count"
        : "weak-matchup-count";

    const rowSelector = rowType === "matchup"
        ? ".matchup-form-row"
        : ".weak-matchup-form-row";

    const grid = document.getElementById(gridId);
    const countInput = document.getElementById(countInputId);

    if (!grid || !countInput) {
        return;
    }

    const rows = grid.querySelectorAll(rowSelector);

    rows.forEach((row, index) => {
        updateRowAttributes(row, rowType, index + 1);
    });

    countInput.value = String(rows.length);
}

function removeDynamicRow(button) {
    const row = button.closest(".matchup-form-row, .weak-matchup-form-row");

    if (!row) {
        return;
    }

    const isMatchupRow = row.classList.contains("matchup-form-row");
    const rowType = isMatchupRow ? "matchup" : "weak";

    row.remove();

    renumberDynamicRows(rowType);
}

function initializeDynamicRowRemoveButtons() {
    document.addEventListener("click", (event) => {
        const button = event.target.closest(".remove-dynamic-row-button");

        if (!button) {
            return;
        }

        removeDynamicRow(button);
    });
}

const STAT_KEYS = [
    "hp",
    "attack",
    "defense",
    "sp_attack",
    "sp_defense",
    "speed",
];

const STAT_DATASET_SUFFIX = {
    hp: "Hp",
    attack: "Attack",
    defense: "Defense",
    sp_attack: "SpAttack",
    sp_defense: "SpDefense",
    speed: "Speed",
};

function getNatureMultiplier(statKey) {
    const natureUpSelect = document.getElementById("nature-up-select");
    const natureDownSelect = document.getElementById("nature-down-select");

    const up = natureUpSelect ? natureUpSelect.value : "none";
    const down = natureDownSelect ? natureDownSelect.value : "none";

    if (statKey === up) {
        return 1.1;
    }

    if (statKey === down) {
        return 0.9;
    }

    return 1.0;
}

function calculateActualStat(statKey, baseStat, point) {
    const safeBase = Number(baseStat || 0);
    const safePoint = Number(point || 0);

    if (statKey === "hp") {
        return Math.floor(((safeBase + safePoint) * 2 + 31) * 0.5 + 60);
    }

    const multiplier = getNatureMultiplier(statKey);

    return Math.floor((((safeBase + safePoint) * 2 + 31) * 0.5 + 5) * multiplier);
}

function getPointValue(statKey) {
    const input = document.querySelector(`.point-input[data-stat="${statKey}"]`);

    if (!input) {
        return 0;
    }

    let value = Number(input.value || 0);

    if (value < 0) {
        value = 0;
        input.value = "0";
    }

    if (value > 32) {
        value = 32;
        input.value = "32";
    }

    return value;
}

function updateStatPreview() {
    const pokemonSelect = document.getElementById("pokemon-select");

    if (!pokemonSelect) {
        return;
    }

    const pokemonId = pokemonSelect.value;
    const statsMap = window.POKEMANE_POKEMON_STATS || {};
    const baseStats = statsMap[pokemonId];

    let pointTotal = 0;

    STAT_KEYS.forEach((statKey) => {
        const point = getPointValue(statKey);
        pointTotal += point;

        const suffix = STAT_DATASET_SUFFIX[statKey];
        const baseElement = document.getElementById(`base-${statKey.replaceAll("_", "-")}`);
        const pointElement = document.getElementById(`point-${statKey.replaceAll("_", "-")}`);
        const actualElement = document.getElementById(`actual-${statKey.replaceAll("_", "-")}`);

        if (!baseStats) {
            if (baseElement) baseElement.textContent = "-";
            if (pointElement) pointElement.textContent = point;
            if (actualElement) actualElement.textContent = "-";
            return;
        }

        const baseStat = baseStats[statKey];
        const actualStat = calculateActualStat(statKey, baseStat, point);

        if (baseElement) baseElement.textContent = baseStat;
        if (pointElement) pointElement.textContent = point;
        if (actualElement) actualElement.textContent = actualStat;
    });

    const totalElement = document.getElementById("point-total");
    const remainingElement = document.getElementById("point-remaining");
    const warningElement = document.getElementById("point-warning");

    if (totalElement) {
        totalElement.textContent = pointTotal;
    }

    if (remainingElement) {
        remainingElement.textContent = Math.max(66 - pointTotal, 0);
    }

    if (warningElement) {
        if (pointTotal > 66) {
            warningElement.classList.remove("hidden");
        } else {
            warningElement.classList.add("hidden");
        }
    }
}

function initializeStatPreview() {
    const pointInputs = document.querySelectorAll(".point-input");
    const natureUpSelect = document.getElementById("nature-up-select");
    const natureDownSelect = document.getElementById("nature-down-select");
    const pokemonSelect = document.getElementById("pokemon-select");

    pointInputs.forEach((input) => {
        input.addEventListener("input", updateStatPreview);
    });

    if (natureUpSelect) {
        natureUpSelect.addEventListener("change", updateStatPreview);
    }

    if (natureDownSelect) {
        natureDownSelect.addEventListener("change", updateStatPreview);
    }

    if (pokemonSelect) {
        pokemonSelect.addEventListener("change", updateStatPreview);
    }

    updateStatPreview();
}



document.addEventListener("DOMContentLoaded", () => {
    const pokemonSelect = document.getElementById("pokemon-select");
    const megaCheckbox = document.getElementById("mega-stone-checkbox");
    const megaSelect = document.getElementById("mega-evolution-select");
    const addMatchupButton = document.getElementById("add-matchup-row-button");
    const addWeakMatchupButton = document.getElementById("add-weak-matchup-row-button");


    updateAbilityOptions();
    updateMegaOptions();
    initializePokemonIconPreviews();
    initializeDynamicRowRemoveButtons();
    initializeStatPreview();
    initializePokemonSelectFilters();


    renumberDynamicRows("matchup");
    renumberDynamicRows("weak");

    if (pokemonSelect) {
        pokemonSelect.addEventListener("change", handlePokemonChange);
    }

    if (megaCheckbox) {
        megaCheckbox.addEventListener("change", () => {
            if (megaSelect) {
                megaSelect.dataset.currentMega = "";
            }

            updateMegaOptions();
        });
    }

    if (addMatchupButton) {
        addMatchupButton.addEventListener("click", () => {
            addDynamicRow(
                "matchup-row-template",
                "matchup-form-grid",
                "matchup-count"
            );
        });
    }

    if (addWeakMatchupButton) {
        addWeakMatchupButton.addEventListener("click", () => {
            addDynamicRow(
                "weak-matchup-row-template",
                "weak-matchup-form-grid",
                "weak-matchup-count"
            );
        });
    }
});