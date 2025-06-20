document.addEventListener('DOMContentLoaded', function () {
  console.log("auth.js: Initializing Firebase auth");
  const HOME_URL = '/'; // Adjust to your homepage URL

  // Retry Firebase initialization if not ready
  function initializeAuth() {
      if (typeof firebase !== 'undefined' && firebase.auth) {
          setupAuthListener();
          handleGoogleRedirect();
      } else {
          console.warn("auth.js: Firebase not ready, retrying...");
          setTimeout(initializeAuth, 500);
      }
  }

  function setupAuthListener() {
      const auth = firebase.auth();
      auth.onAuthStateChanged(user => {
          console.log("auth.js: onAuthStateChanged fired", user ? "User logged in: " + user.uid : "No user");
          const loginBtn = document.getElementById('login-btn');
          const accountDropdown = document.getElementById('account-dropdown');
          const logoutLink = document.getElementById('logout-link');
          const bookmarkButtons = document.querySelectorAll('.bookmark-btn');

          if (user) {
              // Store Firebase token
              user.getIdToken().then(token => {
                  console.log("auth.js: Sending Firebase token to server");
                  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
                  if (!csrfToken) {
                      console.error("auth.js: CSRF token not found");
                      return;
                  }
                  fetch('/set-firebase-token/', {
                      method: 'POST',
                      headers: {
                          'Content-Type': 'application/json',
                          'X-CSRFToken': csrfToken.value
                      },
                      body: JSON.stringify({ firebase_token: token })
                  }).catch(error => {
                      console.error("auth.js: Error storing Firebase token:", error);
                  });
              }).catch(error => {
                  console.error("auth.js: Error getting Firebase token:", error);
              });

              if (loginBtn) loginBtn.style.display = 'none';
              if (accountDropdown) accountDropdown.style.display = 'inline-block';
              bookmarkButtons.forEach(btn => btn.style.display = 'inline-block');

              if (logoutLink) {
                  logoutLink.onclick = () => {
                      auth.signOut().then(() => {
                          console.log("auth.js: User logged out");
                          location.reload();
                      }).catch(error => {
                          console.error("auth.js: Logout error:", error);
                          alert("Failed to log out: " + error.message);
                      });
                  };
              }

              // Redirect from auth page if logged in
              if (window.location.pathname.includes("auth.htm")) {
                  window.location.href = HOME_URL;
              }
          } else {
              if (loginBtn) loginBtn.style.display = 'inline-block';
              if (accountDropdown) accountDropdown.style.display = 'none';
              bookmarkButtons.forEach(btn => btn.style.display = 'none');
          }
      });
  }

  function handleGoogleRedirect() {
      const auth = firebase.auth();
      auth.getRedirectResult()
          .then((result) => {
              if (result.user) {
                  console.log("auth.js: Google Sign-in successful");
                  alert("Google Sign-in successful!");
                  window.location.href = HOME_URL;
              }
          })
          .catch((error) => {
              console.error("auth.js: Google Sign-in error:", error);
              if (error.message) {
                  alert("Google Sign-in error: " + error.message);
              }
          });
  }

  // Modal-based Login/Signup Handling
  let isSignup = false;

  const toggleAuthMode = document.getElementById('toggle-auth-mode');
  if (toggleAuthMode) {
      toggleAuthMode.addEventListener('click', function (e) {
          e.preventDefault();
          isSignup = !isSignup;

          document.getElementById('authModalLabel').innerText = isSignup ? "Signup" : "Login";
          document.getElementById('auth-submit-btn').innerText = isSignup ? "Signup" : "Login";
          document.getElementById('auth-error-msg').textContent = '';

          this.innerHTML = isSignup
              ? ' <a href="#">Login</a>'
              : ' <a href="#">Signup</a>';
      });
  }

  const authForm = document.getElementById('auth-form');
  if (authForm) {
      authForm.addEventListener('submit', function (e) {
          e.preventDefault();
          const email = document.getElementById('auth-email').value.trim();
          const password = document.getElementById('auth-password').value.trim();
          const errorMsg = document.getElementById('auth-error-msg');
          errorMsg.textContent = '';

          const auth = firebase.auth();

          const successHandler = () => {
              console.log("auth.js: Auth successful");
              const modal = bootstrap.Modal.getInstance(document.getElementById('authModal'));
              modal.hide();
              alert(isSignup ? "Account created!" : "Logged in!");
              window.location.href = HOME_URL;
          };

          const errorHandler = (error) => {
              console.error("auth.js: Auth error:", error);
              switch (error.code) {
                  case 'auth/user-not-found':
                      errorMsg.textContent = "❌ Account not registered. Please signup.";
                      break;
                  case 'auth/wrong-password':
                  case 'auth/invalid-login-credentials':
                      errorMsg.textContent = "❌ Incorrect password.";
                      break;
                  case 'auth/email-already-in-use':
                      errorMsg.textContent = "❌ Email already registered. Please login.";
                      break;
                  case 'auth/invalid-email':
                      errorMsg.textContent = "❌ Invalid email format.";
                      break;
                  case 'auth/weak-password':
                      errorMsg.textContent = "❌ Password should be at least 6 characters.";
                      break;
                  default:
                      errorMsg.textContent = "❌ " + error.message;
              }
          };

          if (isSignup) {
              auth.createUserWithEmailAndPassword(email, password)
                  .then(successHandler)
                  .catch(errorHandler);
          } else {
              auth.signInWithEmailAndPassword(email, password)
                  .then(successHandler)
                  .catch(errorHandler);
          }
      });
  }

  // Google Login Button
  const googleLoginBtn = document.getElementById('google-login-btn');
  if (googleLoginBtn) {
      googleLoginBtn.addEventListener('click', () => {
          const provider = new firebase.auth.GoogleAuthProvider();
          firebase.auth().signInWithRedirect(provider);
      });
  }

  // Bookmark Functionality
  document.querySelectorAll('.bookmark-btn').forEach(button => {
      button.addEventListener('click', () => {
          const user = firebase.auth().currentUser;
          if (!user) {
              alert("Please log in to bookmark articles.");
              return;
          }

          const title = button.dataset.title;
          const description = button.dataset.description;
          const image = button.dataset.image;
          const url = button.dataset.url;

          const db = firebase.firestore();
          db.collection('bookmarks')
              .doc(user.uid)
              .collection('articles')
              .add({
                  title: title,
                  description: description,
                  image: image,
                  url: url,
                  timestamp: firebase.firestore.FieldValue.serverTimestamp()
              })
              .then(() => {
                  console.log("auth.js: Article bookmarked");
                  alert("Article bookmarked successfully!");
                  button.disabled = true;
                  button.textContent = "Bookmarked";
              })
              .catch(error => {
                  console.error("auth.js: Error bookmarking article:", error);
                  alert("Failed to bookmark article: " + error.message);
              });
      });
  });

  initializeAuth();
});