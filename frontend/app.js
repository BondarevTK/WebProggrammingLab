window.onload = fetchTweets;

async function fetchTweets() {
  try {
    const response = await fetch("http://localhost:8000/tweet");
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    const tweets = await response.json();
    renderNotes(tweets);
  } catch (error) {
    showError(error.message);
  }
}

function showError(message) {
  const el = document.getElementById("error");
  el.textContent = message;
}

function renderNotes(notes) {
  const container = document.getElementById("tweets");
  container.innerHTML = "";

  for (const note of notes) {
    const card = document.createElement("div");
    card.className = "tweet";

    // Картинка (если есть)
    const img = document.createElement("img");
    img.src = note.imageUrl || "/static/default.jpg"; // фолбэк
    img.alt = note.title;
    img.className = "tweet-image";
    img.loading = "lazy";
    img.onerror = () => {
      img.style.display = "none";
    }; // если картинки нет
    card.appendChild(img);

    // Текстовый блок
    const body = document.createElement("div");
    body.className = "tweet-body";

    const title = document.createElement("h3");
    title.textContent = note.title;

    const desc = document.createElement("p");
    desc.textContent = note.description;

    body.appendChild(title);
    body.appendChild(desc);
    card.appendChild(body);

    card.addEventListener("click", () => showDetails(note));
    container.appendChild(card);
  }
}

const form = document.getElementById("tweetCreateForm");
const titleInput = document.getElementById("createTitle");
const descriptionInput = document.getElementById("createDescription");
const errorBox = document.getElementById("error");
let editingId = null;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.textContent = "";

  const title = titleInput.value.trim();
  const description = descriptionInput.value.trim();

  if (!title || !description) {
    errorBox.textContent = "Заполните оба поля";
    return;
  }

  try {
    let response;
    if (editingId === null) {
      // Создание
      response = await fetch("http://localhost:8000/tweet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description }),
      });
    } else {
      // Обновление
      response = await fetch(`http://localhost:8000/tweet/${editingId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description }),
      });
    }

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    // Сброс формы в режим создания
    titleInput.value = "";
    descriptionInput.value = "";
    editingId = null;

    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.textContent = "Опубликовать";
    submitBtn.classList.add("primary");

    document.getElementById("details").innerHTML = "";
    await fetchTweets();
  } catch (err) {
    errorBox.textContent = "Ошибка: " + err.message;
  }
});

function showDetails(note) {
  const details = document.getElementById("details");
  details.innerHTML = "";

  const title = document.createElement("h2");
  title.textContent = note.title;

  const text = document.createElement("p");
  text.textContent = note.description;

  const actions = document.createElement("div");
  actions.className = "actions";

  const editBtn = document.createElement("button");
  editBtn.textContent = "Редактировать";
  editBtn.addEventListener("click", () => editNote(note.id));

  const deleteBtn = document.createElement("button");
  deleteBtn.textContent = "Удалить";
  deleteBtn.className = "danger";
  deleteBtn.addEventListener("click", () => deleteNote(note.id));

  actions.appendChild(editBtn);
  actions.appendChild(deleteBtn);

  details.appendChild(title);
  details.appendChild(text);
  details.appendChild(actions);
}

async function deleteNote(id) {
  if (!confirm("Удалить эту заметку?")) return;

  try {
    const response = await fetch(`http://localhost:8000/tweet/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${response.status}`);
    }

    // Очищаем панель деталей и перерисовываем список
    document.getElementById("details").innerHTML = "";
    await fetchTweets();
  } catch (err) {
    showError("Ошибка удаления: " + err.message);
  }
}

async function editNote(id) {
  try {
    const response = await fetch(`http://localhost:8000/tweet/${id}`);
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    const note = await response.json();

    titleInput.value = note.title;
    descriptionInput.value = note.description;
    editingId = id;

    // Меняем подпись кнопки
    const submitBtn = form.querySelector("button[type=submit]");
    submitBtn.textContent = "Сохранить";
    submitBtn.classList.remove("primary");

    // Прокручиваем к форме
    form.scrollIntoView({ behavior: "smooth" });
  } catch (error) {
    showError(error.message());
  }
}
