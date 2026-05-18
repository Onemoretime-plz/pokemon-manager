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
    console.log("party_detail.js loaded");

    const refreshButton = document.getElementById("refresh-diagnosis-button");

    if (refreshButton) {
        refreshButton.addEventListener("click", refreshDiagnosis);
    }

    const clearSlotButtons = document.querySelectorAll(".clear-slot-button");

    console.log("clearSlotButtons:", clearSlotButtons.length);

    clearSlotButtons.forEach((button) => {
        button.addEventListener("click", () => {
            clearPartySlot(button.dataset.slotNumber);
        });
    });
});