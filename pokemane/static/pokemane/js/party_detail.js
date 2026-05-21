
function getCookie(name) {
    const cookies = document.cookie ? document.cookie.split(";") : [];

    for (const cookie of cookies) {
        const trimmedCookie = cookie.trim();

        if (trimmedCookie.startsWith(name + "=")) {
            return decodeURIComponent(trimmedCookie.substring(name.length + 1));
        }
    }

    return null;
}

function collectPartySlots() {
    const cards = document.querySelectorAll(".party-set-card");
    const slots = [];

    cards.forEach((card) => {
        const setId = card.dataset.setId;
        const megaActive = card.dataset.megaActive === "true";

        if (!setId) {
            return;
        }

        slots.push({
            set_id: Number(setId),
            mega_active: megaActive,
        });
    });

    return slots;
}

async function refreshDiagnosis() {
    const diagnosisArea = document.getElementById("diagnosis-result");

    if (!diagnosisArea) {
        return;
    }

    const apiUrl = window.POKEMANE_DIAGNOSIS_API_URL;

    if (!apiUrl) {
        console.error("診断APIのURLが設定されていません。");
        return;
    }

    const slots = collectPartySlots();

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                slots: slots,
            }),
        });

        if (!response.ok) {
            throw new Error(`診断APIエラー: ${response.status}`);
        }

        const data = await response.json();
        diagnosisArea.innerHTML = data.html;
    } catch (error) {
        console.error(error);

        diagnosisArea.insertAdjacentHTML(
            "afterbegin",
            '<div class="diagnosis-error">診断結果の更新に失敗しました。</div>'
        );
    }
}

async function clearPartySlot(slotNumber) {
    const apiUrl = window.POKEMANE_CLEAR_SLOT_API_URL;

    if (!apiUrl) {
        console.error("スロット削除APIのURLが設定されていません。");
        return;
    }

    const confirmed = window.confirm(`Slot ${slotNumber} を削除しますか？`);

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                slot_number: Number(slotNumber),
            }),
        });

        if (!response.ok) {
            throw new Error(`スロット削除APIエラー: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error("スロット削除に失敗しました。");
        }

        window.location.reload();
    } catch (error) {
        console.error(error);
        alert("スロット削除に失敗しました。");
    }
}

async function movePartySlot(slotNumber, direction) {
    const apiUrl = window.POKEMANE_MOVE_SLOT_API_URL;

    if (!apiUrl) {
        console.error("スロット移動APIのURLが設定されていません。");
        return;
    }

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                slot_number: Number(slotNumber),
                direction: direction,
            }),
        });

        if (!response.ok) {
            throw new Error(`スロット移動APIエラー: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error("スロット移動に失敗しました。");
        }

        window.location.reload();
    } catch (error) {
        console.error(error);
        alert("スロット移動に失敗しました。");
    }
}


let selectedSlotNumber = null;

function openSetSelectModal(slotNumber) {
    selectedSlotNumber = Number(slotNumber);

    const modal = document.getElementById("set-select-modal");
    const label = document.getElementById("modal-slot-label");

    if (!modal) {
        console.error("型選択モーダルが見つかりません。");
        return;
    }

    if (label) {
        label.textContent = `Slot ${selectedSlotNumber} に追加`;
    }

    modal.classList.remove("hidden");
}

function closeSetSelectModal() {
    const modal = document.getElementById("set-select-modal");

    if (!modal) {
        return;
    }

    modal.classList.add("hidden");
    selectedSlotNumber = null;
}

async function setPartySlot(setId) {
    const apiUrl = window.POKEMANE_SET_SLOT_API_URL;

    if (!apiUrl) {
        console.error("スロット登録APIのURLが設定されていません。");
        return;
    }

    if (!selectedSlotNumber) {
        alert("追加先スロットが選択されていません。");
        return;
    }

    try {
        const response = await fetch(apiUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                slot_number: selectedSlotNumber,
                set_id: Number(setId),
            }),
        });

        if (!response.ok) {
            throw new Error(`スロット登録APIエラー: ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error("スロット登録に失敗しました。");
        }

        window.location.reload();
    } catch (error) {
        console.error(error);
        alert("スロット登録に失敗しました。");
    }
}

function filterSetOptions(keyword) {
    const normalizedKeyword = keyword.trim().toLowerCase();
    const options = document.querySelectorAll(".modal-set-option");

    options.forEach((option) => {
        const searchText = (option.dataset.searchText || "").toLowerCase();

        if (!normalizedKeyword || searchText.includes(normalizedKeyword)) {
            option.classList.remove("hidden");
        } else {
            option.classList.add("hidden");
        }
    });
}

function replaceTypeClass(element, newClass) {
    if (!element) {
        return;
    }

    const typeColorClasses = [
        "type-normal",
        "type-fire",
        "type-water",
        "type-electric",
        "type-grass",
        "type-ice",
        "type-fighting",
        "type-poison",
        "type-ground",
        "type-flying",
        "type-psychic",
        "type-bug",
        "type-rock",
        "type-ghost",
        "type-dragon",
        "type-dark",
        "type-steel",
        "type-fairy",
        "type-unknown",
    ];

    typeColorClasses.forEach((className) => {
        element.classList.remove(className);
    });

    if (newClass) {
        element.classList.add(newClass);
    }

    element.classList.add("type-badge");
}

function updateCardDisplayForMegaState(card, megaActive) {
    const prefix = megaActive ? "mega" : "base";

    const pokemonName = card.dataset[`${prefix}Name`];
    const iconUrl = card.dataset[`${prefix}IconUrl`];
    const type1 = card.dataset[`${prefix}Type1`];
    const type2 = card.dataset[`${prefix}Type2`];
    const type1Class = card.dataset[`${prefix}Type1Class`];
    const type2Class = card.dataset[`${prefix}Type2Class`];
    const ability = card.dataset[`${prefix}Ability`];

    const nameElement = card.querySelector(".card-pokemon-name");
    if (nameElement) {
        nameElement.textContent = pokemonName;
    }

    const iconElement = card.querySelector(".card-pokemon-icon");
    const placeholderElement = card.querySelector(".card-pokemon-icon-placeholder");

    if (iconElement) {
        if (iconUrl) {
            iconElement.src = iconUrl;
            iconElement.alt = pokemonName;
            iconElement.classList.remove("hidden");
        } else {
            iconElement.classList.add("hidden");
        }
    }

    if (placeholderElement) {
        if (iconUrl) {
            placeholderElement.classList.add("hidden");
        } else {
            placeholderElement.classList.remove("hidden");
        }
    }

    const type1Element = card.querySelector(".card-type1");
    if (type1Element) {
        type1Element.textContent = type1;
        replaceTypeClass(type1Element, type1Class);
    }

    const type2Element = card.querySelector(".card-type2");
    if (type2Element) {
        type2Element.textContent = type2;
        replaceTypeClass(type2Element, type2Class);

        if (type2) {
            type2Element.classList.remove("hidden");
        } else {
            type2Element.classList.add("hidden");
        }
    }

    const abilityElement = card.querySelector(".card-ability-name");
    if (abilityElement) {
        abilityElement.textContent = ability;
    }

    const statMap = {
        hp: "Hp",
        attack: "Attack",
        defense: "Defense",
        spAttack: "SpAttack",
        spDefense: "SpDefense",
        speed: "Speed",
    };

    const statSelectors = {
        hp: ".card-stat-hp",
        attack: ".card-stat-attack",
        defense: ".card-stat-defense",
        spAttack: ".card-stat-sp-attack",
        spDefense: ".card-stat-sp-defense",
        speed: ".card-stat-speed",
    };

    Object.entries(statSelectors).forEach(([key, selector]) => {
        const element = card.querySelector(selector);

        if (!element) {
            return;
        }

        const datasetKey = `${prefix}${statMap[key]}`;
        element.textContent = card.dataset[datasetKey];
    });
}

function toggleMegaState(button) {
    const slotNumber = button.dataset.slotNumber;
    const card = document.querySelector(
        `.party-set-card[data-slot-number="${slotNumber}"]`
    );

    if (!card) {
        console.error(`Slot ${slotNumber} のカードが見つかりません。`);
        return;
    }

    const currentMegaActive = card.dataset.megaActive === "true";
    const nextMegaActive = !currentMegaActive;

    card.dataset.megaActive = nextMegaActive ? "true" : "false";
    button.dataset.megaActive = nextMegaActive ? "true" : "false";

    if (nextMegaActive) {
        button.textContent = "メガON";
        button.classList.add("is-active");
    } else {
        button.textContent = "メガOFF";
        button.classList.remove("is-active");
    }

    updateCardDisplayForMegaState(card, nextMegaActive);
    refreshDiagnosis();
}

document.addEventListener("DOMContentLoaded", () => {

    const refreshButton = document.getElementById("refresh-diagnosis-button");

    if (refreshButton) {
        refreshButton.addEventListener("click", refreshDiagnosis);
    }

    const moveSlotButtons = document.querySelectorAll(".move-slot-button");

    moveSlotButtons.forEach((button) => {
        button.addEventListener("click", () => {
            movePartySlot(button.dataset.slotNumber, button.dataset.direction);
        });
    });


    const clearSlotButtons = document.querySelectorAll(".clear-slot-button");

    clearSlotButtons.forEach((button) => {
        button.addEventListener("click", () => {
            clearPartySlot(button.dataset.slotNumber);
        });
    });

    const emptySlots = document.querySelectorAll(".selectable-empty-slot");

    emptySlots.forEach((slot) => {
        slot.addEventListener("click", () => {
            openSetSelectModal(slot.dataset.slotNumber);
        });
    });

    const megaToggleButtons = document.querySelectorAll(".mega-toggle-button");

    megaToggleButtons.forEach((button) => {
        button.addEventListener("click", () => {
            toggleMegaState(button);
        });
    });

    const closeModalButton = document.getElementById("close-set-modal-button");

    if (closeModalButton) {
        closeModalButton.addEventListener("click", closeSetSelectModal);
    }

    const modal = document.getElementById("set-select-modal");

    if (modal) {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                closeSetSelectModal();
            }
        });
    }

    const setOptions = document.querySelectorAll(".modal-set-option");

    setOptions.forEach((option) => {
        option.addEventListener("click", () => {
            setPartySlot(option.dataset.setId);
        });
    });

    const setSearchInput = document.getElementById("set-search-input");

    if (setSearchInput) {
        setSearchInput.addEventListener("input", () => {
            filterSetOptions(setSearchInput.value);
        });
    }
});