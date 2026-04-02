document.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const page = body.dataset.page || "";

    if (page === "results" && body.dataset.locationNeeded === "true") {
        requestLocationForResults();
    }

    setupRegisterValidation();
    setupDeleteConfirmation();
    setupCenterFormValidation();
});

function requestLocationForResults() {
    const geoStatus = document.getElementById("geo-status");
    if (!navigator.geolocation) {
        window.location.href = "/results?error=unsupported";
        return;
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;
            window.location.href = `/results?lat=${lat}&lng=${lng}`;
        },
        (error) => {
            let errorMsg = "location";
            if (error.code === error.PERMISSION_DENIED) {
                errorMsg = "permission_denied";
            } else if (error.code === error.POSITION_UNAVAILABLE) {
                errorMsg = "unavailable";
            } else if (error.code === error.TIMEOUT) {
                errorMsg = "timeout";
            }
            window.location.href = `/results?error=${errorMsg}`;
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0,
        }
    );

    if (geoStatus) {
        geoStatus.querySelector("span").textContent = "Requesting your location permission from browser...";
    }
}

function setupRegisterValidation() {
    const registerForm = document.getElementById("register-form");
    if (!registerForm) {
        return;
    }

    registerForm.addEventListener("submit", (event) => {
        const password = document.getElementById("password").value;
        const confirmPassword = document.getElementById("confirm_password").value;

        if (password.length < 4) {
            event.preventDefault();
            alert("Password must be at least 4 characters long.");
            return;
        }

        if (password !== confirmPassword) {
            event.preventDefault();
            alert("Password and confirm password must match.");
        }
    });
}

function setupDeleteConfirmation() {
    const deleteForms = document.querySelectorAll("form[data-confirm-delete='true']");
    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const ok = confirm("Delete this waste center? This action cannot be undone.");
            if (!ok) {
                event.preventDefault();
            }
        });
    });
}

function setupCenterFormValidation() {
    const centerForm = document.getElementById("center-form");
    if (!centerForm) {
        return;
    }

    centerForm.addEventListener("submit", (event) => {
        const lat = Number(document.getElementById("latitude").value);
        const lng = Number(document.getElementById("longitude").value);
        const price = Number(document.getElementById("price_per_kg").value);

        if (Number.isNaN(lat) || lat < -90 || lat > 90) {
            event.preventDefault();
            alert("Latitude must be between -90 and 90.");
            return;
        }

        if (Number.isNaN(lng) || lng < -180 || lng > 180) {
            event.preventDefault();
            alert("Longitude must be between -180 and 180.");
            return;
        }

        if (Number.isNaN(price) || price < 0) {
            event.preventDefault();
            alert("Price per kg must be 0 or more.");
        }
    });
}