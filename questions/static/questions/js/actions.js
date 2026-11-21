function showActionError(message) {
  const notice = document.querySelector("#action-error");
  notice.textContent = message;
  notice.hidden = !message;
}

async function sendAction(form, data) {
  showActionError("");
  try {
    const response = await fetch(form.action, {
      method: "POST",
      body: data,
      headers: {"Accept": "application/json"},
    });
    const result = await response.json();
    if (response.status === 401 && result.login_url) {
      const login = new URL(result.login_url, window.location.origin);
      login.searchParams.set("next", window.location.pathname + window.location.search);
      window.location.assign(login);
    }
    if (!response.ok) {
      showActionError(result.error || "Не удалось сохранить изменение.");
    }
    return result;
  } catch {
    showActionError("Не удалось связаться с сервером. Повторите попытку.");
    return {};
  }
}

document.querySelectorAll("[data-vote-form]").forEach((form) => {
  const buttons = [...form.querySelectorAll("button")];
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = new FormData(form);
    data.set("value", event.submitter.value);
    const previous = buttons.find((button) => button.getAttribute("aria-pressed") === "true");
    buttons.forEach((button) => { button.disabled = true; });
    const result = await sendAction(form, data);
    if (result.rating !== undefined) {
      form.querySelector("[data-rating]").textContent = result.rating;
    }
    buttons.forEach((button) => {
      const selected = result.my_vote === undefined ? button === previous : Number(button.value) === result.my_vote;
      button.setAttribute("aria-pressed", String(selected));
      button.disabled = selected;
    });
  });
});

const correctForms = [...document.querySelectorAll("[data-correct-form]")];
correctForms.forEach((form) => {
  const checkbox = form.querySelector('input[type="checkbox"]');
  checkbox.addEventListener("change", async () => {
    const selected = checkbox.checked;
    const controls = correctForms.map((item) => item.querySelector('input[type="checkbox"]'));
    controls.forEach((control) => { control.disabled = true; });
    const data = new FormData(form);
    data.set("selected", selected ? "1" : "0");
    const result = await sendAction(form, data);
    checkbox.checked = result.selected ?? !selected;
    if (result.cleared) {
      for (const id of result.cleared) {
        const previous = document.getElementById(`correct-${id}`);
        if (previous) previous.checked = false;
      }
    }
    controls.forEach((control) => { control.disabled = false; });
  });
});
