document.addEventListener("DOMContentLoaded", () => {
  const fileInputs = document.querySelectorAll("[data-file-input]");

  fileInputs.forEach((input) => {
    input.addEventListener("change", () => {
      const targetId = input.getAttribute("data-target");
      if (!targetId) {
        return;
      }

      const target = document.getElementById(targetId);
      if (!target) {
        return;
      }

      const fileName = input.files && input.files.length > 0 ? input.files[0].name : "No file selected";
      target.textContent = fileName;
    });
  });
});