document.addEventListener('DOMContentLoaded', function () {
  // باز/بسته کردن منو موبایل
  var navToggle = document.querySelector('.nav-toggle');
  var mainNav = document.querySelector('.main-nav');
  if (navToggle && mainNav) {
    navToggle.addEventListener('click', function () {
      mainNav.classList.toggle('is-open');
      mainNav.style.display = mainNav.classList.contains('is-open') ? 'flex' : '';
    });
  }

  // دکمه‌های + / - برای فیلد تعداد
  document.querySelectorAll('.qty-input').forEach(function (wrap) {
    var input = wrap.querySelector('input[type="number"]');
    var minus = wrap.querySelector('[data-qty="minus"]');
    var plus = wrap.querySelector('[data-qty="plus"]');
    if (!input) return;

    if (minus) {
      minus.addEventListener('click', function () {
        var value = parseInt(input.value || '1', 10);
        var min = parseInt(input.min || '1', 10);
        input.value = Math.max(min, value - 1);
      });
    }
    if (plus) {
      plus.addEventListener('click', function () {
        var value = parseInt(input.value || '1', 10);
        var max = parseInt(input.max || '99', 10);
        input.value = Math.min(max, value + 1);
      });
    }
  });

  // بستن خودکار پیام‌ها بعد از چند ثانیه
  document.querySelectorAll('.messages .alert').forEach(function (alertEl) {
    setTimeout(function () {
      alertEl.style.transition = 'opacity .4s ease';
      alertEl.style.opacity = '0';
      setTimeout(function () { alertEl.remove(); }, 400);
    }, 5000);
  });
});
