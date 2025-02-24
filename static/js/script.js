

const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if(entry.isIntersecting){
            entry.target.classList.add('show');
        } else{
            entry.target.classList.remove('show');
        }
    })
})

const hiddenElements = document.querySelectorAll(".hero, .features, .cta");

hiddenElements.forEach((el) => observer.observe(el));

// 🔍 Toggle Search Overlay
function toggleSearch() {
    const searchOverlay = document.getElementById("searchOverlay");
    searchOverlay.style.display = (searchOverlay.style.display === "flex") ? "none" : "flex";
    document.getElementById("searchInput").focus();
}

function toggleUserMenu() {
  let menu = document.getElementById("userMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// Close the dropdown when clicking outside
document.addEventListener("click", function(event) {
  let menu = document.getElementById("userMenu");
  let userIcon = document.querySelector(".user-icon");

  if (!userIcon.contains(event.target) && !menu.contains(event.target)) {
      menu.style.display = "none";
  }
});



function fetchSuggestions() {
  let query = document.getElementById("searchInput").value.trim();
  let suggestionsBox = document.getElementById("searchSuggestions");

  let url = query.length > 0 ? `/search-suggestions?q=${query}` : `/popular-jobs`;

  fetch(url)
      .then(response => response.json())
      .then(data => {
          suggestionsBox.innerHTML = "";
          suggestionsBox.style.display = "block"; // Ensure suggestions are always visible

          if (!data.suggestions || data.suggestions.length === 0) {
              suggestionsBox.innerHTML = "<li class='no-results'>No results found</li>";
              return;
          }

          data.suggestions.forEach(suggestion => {
              let listItem = document.createElement("li");

              // Trim extra whitespace & remove unintended formatting
              listItem.textContent = suggestion.replace(/\s+/g, ' ').trim();
              listItem.classList.add("suggestion-item");

              listItem.onclick = function () {
                  document.getElementById("searchInput").value = suggestion;
                  window.location.href = `/search?q=${encodeURIComponent(suggestion)}`;
              };

              suggestionsBox.appendChild(listItem);
          });
      })
      .catch(error => console.error("Error fetching search suggestions:", error));
}


// Pre-populate trending jobs
function loadTrendingJobs() {
  let suggestionsBox = document.getElementById("searchSuggestions");

  fetch(`/popular-jobs`)
      .then(response => response.json())
      .then(data => {
          suggestionsBox.innerHTML = "";

          data.suggestions.forEach(suggestion => {
              let listItem = document.createElement("li");
              listItem.textContent = suggestion;
              listItem.onclick = function () {
                  document.getElementById("searchInput").value = suggestion;
                  fetchSuggestions();
              };
              suggestionsBox.appendChild(listItem);
          });
      });
}

// Open and load trending jobs
function openSearch() {
  document.getElementById("searchOverlay").style.display = "flex";
  document.getElementById("searchInput").focus();
  loadTrendingJobs();
}

function closeSearch() {
  document.getElementById("searchOverlay").style.display = "none";
  document.getElementById("searchSuggestions").innerHTML = "";
}

function selectSuggestion(suggestion) {
  document.getElementById("searchInput").value = suggestion;
  fetchSuggestions();
}




// 🔄 User Dropdown Toggle
function toggleUserMenu() {
  let menu = document.getElementById("userMenu");
  menu.style.display = (menu.style.display === "block") ? "none" : "block";
}

// 🛑 Close User Menu when Clicking Outside
document.addEventListener("click", function (event) {
  let menu = document.getElementById("userMenu");
  let userIcon = document.querySelector(".user-icon");

  if (menu && userIcon && !userIcon.contains(event.target) && !menu.contains(event.target)) {
      menu.style.display = "none";
  }
});

// ✨ Display Suggestions Dynamically
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchInput");
  const suggestionsContainer = document.getElementById("searchSuggestions");

  searchInput.addEventListener("input", function () {
      const query = searchInput.value.trim();
      if (query.length < 2) {
          suggestionsContainer.innerHTML = "";
          return;
      }

      fetch(`/search-suggestions?q=${query}`)
          .then(response => response.json())
          .then(data => {
              suggestionsContainer.innerHTML = ""; // Clear previous results
              if (!data.suggestions || data.suggestions.length === 0) {
                  suggestionsContainer.innerHTML = "<li>No results found</li>";
                  return;
              }

              data.suggestions.forEach(job => {
                  const jobElement = document.createElement("li");
                  jobElement.innerHTML = `<a href="/job/${job.id}">${job.title} - ${job.location}</a>`;
                  suggestionsContainer.appendChild(jobElement);
              });
          })
          .catch(error => console.error("Error fetching search results:", error));
  });
});

// Select elements
const hamburger = document.querySelector(".hamburger");
const navLinks = document.querySelector(".nav-links");

// Toggle menu on click
hamburger.addEventListener("click", () => {
  navLinks.classList.toggle("active"); // Show/hide menu
  hamburger.classList.toggle("open"); // Toggle animation
});

// Close menu when a link is clicked
document.querySelectorAll(".nav-links a").forEach(link => {
  link.addEventListener("click", () => {
    navLinks.classList.remove("active"); // Close menu
    hamburger.classList.remove("open"); // Reset icon
  });
});

document.addEventListener("DOMContentLoaded", function () {
  const noteInput = document.getElementById("note-input");
  const notesContainer = document.getElementById("notes-container");

  noteInput.addEventListener("keypress", function (event) {
      if (event.key === "Enter" && noteInput.value.trim() !== "") {
          event.preventDefault();
          
          const noteText = noteInput.value.trim();
          addNote(noteText);

          // Send the note to the backend (optional)
          fetch(window.location.pathname + "/add_note", {
              method: "POST",
              headers: {
                  "Content-Type": "application/json"
              },
              body: JSON.stringify({ note: noteText })
          });

          noteInput.value = ""; // Clear input field
      }
  });

  function addNote(text) {
      const noteElement = document.createElement("div");
      noteElement.classList.add("note");
      noteElement.innerHTML = `
          <p class="note-text">"${text}"</p>
          <p class="note-meta">— Just now</p>
      `;
      notesContainer.prepend(noteElement);
  }
});
