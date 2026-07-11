const CONTACT_EMAIL = "lucasrimbano@gmail.com";

const contactForm = document.querySelector("#contactForm");
const contactStatus = document.querySelector("#contactStatus");

function setStatus(message, type = "info") {
    if (!contactStatus) return;

    contactStatus.textContent = message;
    contactStatus.dataset.type = type;
}

function buildMailtoUrl(formData) {
    const name = formData.get("name").trim();
    const email = formData.get("email").trim();
    const service = formData.get("service").trim();
    const message = formData.get("message").trim();

    const subject = `Solicitud de servicio: ${service} - ${name}`;
    const body = [
        `Nombre: ${name}`,
        `Email: ${email}`,
        `Servicio solicitado: ${service}`,
        "",
        "Mensaje:",
        message,
        "",
        "Consulta enviada desde la demo de Crypto Dashboard para solicitar una version personalizada del servicio.",
    ].join("\n");

    return `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

if (contactForm) {
    contactForm.addEventListener("submit", (event) => {
        event.preventDefault();

        if (!contactForm.checkValidity()) {
            contactForm.classList.add("was-validated");
            setStatus("Completa todos los campos para preparar el email.", "error");
            return;
        }

        const formData = new FormData(contactForm);
        const mailtoUrl = buildMailtoUrl(formData);

        window.location.href = mailtoUrl;
        setStatus("Se abrio tu cliente de correo con la consulta lista para enviar.", "success");
        contactForm.reset();
        contactForm.classList.remove("was-validated");
    });
}
