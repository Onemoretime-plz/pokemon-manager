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

document.addEventListener("DOMContentLoaded", () => {
    const refreshButton = document.getElementById("refresh-diagnosis-button");

    if (refreshButton) {
        refreshButton.addEventListener("click", refreshDiagnosis);
    }

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

let selectedSlotNumber = null;

function openSetSelectModal(slotNumber) {
    selectedSlotNumber = Number(slotNumber);

    const modal = document.getElementById("set-select-modal");
    const label = document.getElementById("modal-slot-label");

    if (!modal) {
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
        const searchText = option.dataset.searchText.toLowerCase();

        if (!normalizedKeyword || searchText.includes(normalizedKeyword)) {
            option.classList.remove("hidden");
        } else {
            option.classList.add("hidden");
        }
    });
}