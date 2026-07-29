(() => {
  const button = document.querySelector("[data-copy-email]");
  const status = document.querySelector("[data-copy-status]");
  if (!button || !status) return;

  const showManualFallback = (email) => {
    status.textContent = `Email ready to copy manually: ${email}`;
    button.textContent = "Copy manually";
  };

  button.addEventListener("click", async () => {
    const email = button.dataset.copyEmail;
    const canCopy =
      navigator.clipboard &&
      typeof navigator.clipboard.writeText === "function";

    if (!canCopy) {
      showManualFallback(email);
      return;
    }

    try {
      await navigator.clipboard.writeText(email);
      status.textContent = "Email copied.";
      button.textContent = "Copied";
    } catch (error) {
      showManualFallback(email);
    }
  });
})();
