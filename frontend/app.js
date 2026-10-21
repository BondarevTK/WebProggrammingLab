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

async function showDetails(note) {
  try {
    const response = await fetch(`http://localhost:8000/tweet/${note.id}`);
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    const thisTweet = await response.json();
    const details = document.getElementById("details");
    details.innerHTML = "";

    // --- Заголовок и текст поста ---
    const title = document.createElement("h2");
    title.textContent = thisTweet.title;

    const text = document.createElement("p");
    text.textContent = thisTweet.description;

    // --- Кнопки действий ---
    const actions = document.createElement("div");
    actions.className = "actions";

    const editBtn = document.createElement("button");
    editBtn.textContent = "Редактировать";
    editBtn.addEventListener("click", () => editNote(thisTweet.id));

    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Удалить";
    deleteBtn.className = "danger";
    deleteBtn.addEventListener("click", () => deleteNote(thisTweet.id));

    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);

    // --- Секция комментариев ---
    const commentsSection = document.createElement("div");
    commentsSection.className = "comments-section";

    const commentsTitle = document.createElement("h3");
    commentsTitle.textContent = "Комментарии";
    commentsSection.appendChild(commentsTitle);

    // Проверяем, есть ли комментарии и не пустой ли массив
    if (thisTweet.comments && thisTweet.comments.length > 0) {
      thisTweet.comments.forEach((comment) => {
        const commentDiv = document.createElement("div");
        commentDiv.className = "comment-item";

        // Верхняя часть комментария: текст, лайки и кнопка удаления
        const commentHeader = document.createElement("div");
        commentHeader.className = "comment-header";

        const commentText = document.createElement("p");
        commentText.textContent = comment.description;

        const commentActions = document.createElement("div");
        commentActions.className = "comment-actions";

        const commentLikes = document.createElement("span");
        commentLikes.className = "comment-likes";
        commentLikes.textContent = `❤️ ${comment.likes || 0}`;

        // 👇 Кнопка удаления комментария
        const deleteCommentBtn = document.createElement("button");
        deleteCommentBtn.textContent = "✖";
        deleteCommentBtn.className = "delete-comment-btn";
        deleteCommentBtn.title = "Удалить комментарий";

        // Обработчик клика
        deleteCommentBtn.addEventListener("click", (e) => {
          e.stopPropagation(); // Чтобы клик не триггерил другие события
          deleteComment(comment.id, thisTweet.id);
        });

        commentActions.appendChild(commentLikes);
        commentActions.appendChild(deleteCommentBtn);

        commentHeader.appendChild(commentText);
        commentHeader.appendChild(commentActions);

        commentDiv.appendChild(commentHeader);
        commentsSection.appendChild(commentDiv);
      });
    } else {
      const noComments = document.createElement("p");
      noComments.className = "no-comments";
      noComments.textContent = "Пока нет комментариев. Будьте первым!";
      commentsSection.appendChild(noComments);
    }
    details.appendChild(title);
    details.appendChild(text);
    details.appendChild(actions);
    details.appendChild(commentsSection); // Добавляем комментарии в конец

    const addCommentForm = document.createElement("form");
    addCommentForm.className = "add-comment-form";

    const commentInput = document.createElement("input");
    commentInput.type = "text";
    commentInput.placeholder = "Написать комментарий...";
    commentInput.required = true;

    const submitCommentBtn = document.createElement("button");
    submitCommentBtn.type = "submit";
    submitCommentBtn.textContent = "Отправить";

    addCommentForm.appendChild(commentInput);
    addCommentForm.appendChild(submitCommentBtn);
    commentsSection.appendChild(addCommentForm);

    addCommentForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = commentInput.value.trim();
      if (!text) return;

      try {
        const response = await fetch(
          `http://localhost:8000/tweet/${note.id}/comments`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ description: text }), // Отправляем только текст
          },
        );

        if (!response.ok) throw new Error("Ошибка при отправке");

        // Перезапрашиваем данные твита, чтобы увидеть новый комментарий
        // (или можно вручную добавить DOM-элемент, но перезапрос надежнее)
        const updatedNote = await (
          await fetch(`http://localhost:8000/tweet/${note.id}`)
        ).json();
        showDetails(updatedNote);
      } catch (err) {
        alert("Не удалось добавить комментарий: " + err.message);
      }
    });
  } catch (error) {
    showError(error.message);
  }

  // --- Сборка всего вместе ---
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

async function deleteComment(commentId, tweetId) {
  if (!confirm("Удалить этот комментарий?")) return;

  try {
    // В вашем скриншоте эндпоинт выглядит как /tweet/comments (без ID в URL)
    // Если в бэкенде FastAPI параметр объявлен просто как commentId: int,
    // то FastAPI автоматически ищет его в Query Parameters (после вопросительного знака).
    const response = await fetch(
      `http://localhost:8000/tweet/${tweetId}/comments/${commentId}`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      throw new Error(`Ошибка удаления: ${response.status}`);
    }

    // Перезапрашиваем твит, чтобы обновить список комментариев на экране
    const updatedNote = await (
      await fetch(`http://localhost:8000/tweet/${tweetId}`)
    ).json();
    showDetails(updatedNote);
  } catch (err) {
    alert(err.message);
  }
}
