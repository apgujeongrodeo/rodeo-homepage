const form = document.querySelector('#qa-form');
const receipt = document.querySelector('#qa-receipt');

form.addEventListener('submit', () => {
  const category = document.querySelector('#qa-category').value;
  const visibility = document.querySelector('#qa-visibility').value;
  const question = document.querySelector('#qa-body').value.trim();
  document.querySelector('#qa-payload').value = `[${visibility}] [${category}]\n${question}`;
  receipt.showModal();
});

receipt.querySelector('button').addEventListener('click', () => receipt.close());
form.querySelector('button[type=submit]').disabled = false;
