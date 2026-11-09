(() => {
  const form = document.getElementById("sale-form");
  const tokenInput = document.getElementById("staff-token");
  const amountInput = document.getElementById("amount");
  const issueButton = document.getElementById("issue-button");
  const resultCard = document.getElementById("result-card");
  const emptyResult = document.getElementById("empty-result");
  const claimResult = document.getElementById("claim-result");
  const resultMessage = document.getElementById("result-message");
  const paidRadios = Array.from(document.querySelectorAll('input[name="paid"]'));

  const isPaid = () =>
    paidRadios.some((radio) => radio.checked && radio.value === "yes");

  function updateButton() {
    issueButton.disabled =
      !tokenInput.value.trim() ||
      !amountInput.value ||
      !amountInput.checkValidity() ||
      !isPaid();
  }

  function showMessage(message, kind = "error") {
    resultMessage.textContent = message;
    resultMessage.dataset.kind = kind;
    resultMessage.hidden = false;
  }

  function newPurchaseReference() {
    if (crypto.randomUUID) return crypto.randomUUID();
    const bytes = crypto.getRandomValues(new Uint8Array(16));
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function clearResult() {
    claimResult.hidden = true;
    emptyResult.hidden = false;
    resultMessage.hidden = true;
    resultCard.hidden = false;
  }

  [tokenInput, amountInput, ...paidRadios].forEach((input) => {
    input.addEventListener("input", updateButton);
    input.addEventListener("change", updateButton);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!isPaid() || !form.reportValidity()) return;

    issueButton.disabled = true;
    issueButton.textContent = "Preparing QR…";
    resultMessage.hidden = true;
    clearResult();

    try {
      const response = await fetch("/api/purchase/earn", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Staff-Token": tokenInput.value,
        },
        body: JSON.stringify({
          amount_qar: amountInput.value,
          paid: true,
          purchase_reference: newPurchaseReference(),
        }),
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.error || "We couldn't issue the points QR.");
      }

      emptyResult.hidden = true;
      if (!result.claim_code || !result.qr_image) {
        claimResult.hidden = true;
        showMessage(
          "This purchase is below QAR 10, so it did not earn a point or generate a QR.",
          "success",
        );
        return;
      }

      document.getElementById("points-earned").textContent =
        String(result.points_earned);
      document.getElementById("claim-qr").src = result.qr_image;
      claimResult.hidden = false;
    } catch (error) {
      emptyResult.hidden = false;
      showMessage(error.message || "Something went wrong. Please try again.");
    } finally {
      issueButton.innerHTML = 'Issue points QR <span aria-hidden="true">↗</span>';
      updateButton();
    }
  });

  resultCard.hidden = false;
  updateButton();
})();
