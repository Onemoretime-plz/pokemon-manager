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

function initializePokemonIconPreviews() {
    const selects = document.querySelectorAll(".pokemon-icon-select");

    selects.forEach((selectElement) => {
        updatePokemonIconPreview(selectElement);

        selectElement.addEventListener("change", () => {
            updatePokemonIconPreview(selectElement);
        });
    });
}


document.addEventListener("DOMContentLoaded", () => {
    const pokemonSelect = document.getElementById("pokemon-select");
    const megaCheckbox = document.getElementById("mega-stone-checkbox");
    const megaSelect = document.getElementById("mega-evolution-select");

    updateAbilityOptions();
    updateMegaOptions();
    initializePokemonIconPreviews();

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
});