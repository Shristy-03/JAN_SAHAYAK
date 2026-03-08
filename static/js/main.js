// ===============================
// 1️⃣ Show Auto Hide Messages
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const messages = document.querySelectorAll(".message");

    messages.forEach(msg => {
        setTimeout(() => {
            msg.style.display = "none";
        }, 3000);
    });
});


// ===============================
// 2️⃣ Simple Login Validation
// ===============================

function validateLogin() {
    const username = document.querySelector("input[name='username']").value;
    const password = document.querySelector("input[name='password']").value;

    if (username === "" || password === "") {
        alert("Please fill all fields!");
        return false;
    }
    return true;
}


// ===============================
// 3️⃣ Complaint Form Validation
// ===============================

function validateComplaint() {
    const area = document.querySelector("input[name='area']").value;

    if (area.length < 3) {
        alert("Area name must be at least 3 characters long!");
        return false;
    }

    return true;
}


// ===============================
// 4️⃣ Status Color Highlighting
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const statusCells = document.querySelectorAll("td");

    statusCells.forEach(cell => {
        if (cell.innerText === "Pending") {
            cell.style.color = "orange";
        }
        if (cell.innerText === "In Progress") {
            cell.style.color = "blue";
        }
        if (cell.innerText === "Resolved") {
            cell.style.color = "green";
        }
    });
});


// ===============================
// 5️⃣ Prediction Risk Indicator
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const rows = document.querySelectorAll("table tr");

    rows.forEach(row => {
        const cells = row.getElementsByTagName("td");
        if (cells.length > 1) {
            const count = parseInt(cells[1].innerText);

            if (count > 10) {
                row.style.backgroundColor = "#ffcccc"; // High risk
            } else if (count > 5) {
                row.style.backgroundColor = "#fff3cd"; // Medium risk
            } else {
                row.style.backgroundColor = "#d4edda"; // Low risk
            }
        }
    });
});


// ===============================
// 6️⃣ Navbar Active Highlight
// ===============================

document.addEventListener("DOMContentLoaded", function () {
    const links = document.querySelectorAll("nav a");
    const currentURL = window.location.pathname;

    links.forEach(link => {
        if (link.getAttribute("href") === currentURL) {
            link.style.fontWeight = "bold";
            link.style.textDecoration = "underline";
        }
    });
});



document.addEventListener("DOMContentLoaded", function () {

const chatbotBtn = document.getElementById("chatbot-button");

if(chatbotBtn){
chatbotBtn.onclick=function(){
document.getElementById("chatbot-box").style.display="flex"
}
}

});

function closeChat(){
document.getElementById("chatbot-box").style.display="none"
}

function sendMessage(){

let input = document.getElementById("chatInput")
let msg = input.value

if(msg.trim() === ""){
return
}

let chat = document.getElementById("chatbot-messages")

chat.innerHTML += `<p><b>You:</b> ${msg}</p>`

fetch("/chatbot-api/", {
  method: "POST",
  headers: {
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    message: msg
  })
})
.then(res => res.json())
.then(data => {
  chat.innerHTML += `<p><b>Bot:</b> ${data.reply}</p>`
})

input.value=""
}


function getCookie(name) {
let cookieValue = null;

if (document.cookie && document.cookie !== '') {
const cookies = document.cookie.split(';');

for (let i = 0; i < cookies.length; i++) {
const cookie = cookies[i].trim();

if (cookie.substring(0, name.length + 1) === (name + '=')) {
cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
break;
}
}
}

return cookieValue;
}