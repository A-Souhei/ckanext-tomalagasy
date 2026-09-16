// moment.js ships no Malagasy locale, so CKAN's client-side date rewrite
// (base/javascript/main.js calls moment.locale(<html lang>)) silently fell back
// to English month names on `mg` pages. Names and formats follow CLDR, the same
// data Babel uses for the server-rendered dates.
(function () {
  if (typeof moment === "undefined" || moment.locales().indexOf("mg") !== -1) {
    return;
  }
  // defineLocale also switches the global locale; restore it so pages in other
  // languages are unaffected.
  var current = moment.locale();
  moment.defineLocale("mg", {
    months: "Janoary_Febroary_Martsa_Aprily_Mey_Jona_Jolay_Aogositra_Septambra_Oktobra_Novambra_Desambra".split("_"),
    monthsShort: "Jan_Feb_Mar_Apr_Mey_Jon_Jol_Aog_Sep_Okt_Nov_Des".split("_"),
    weekdays: "Alahady_Alatsinainy_Talata_Alarobia_Alakamisy_Zoma_Asabotsy".split("_"),
    weekdaysShort: "Alah_Alats_Tal_Alar_Alak_Zom_Asab".split("_"),
    weekdaysMin: "Ah_Al_Ta_Ar_Ak_Zo_As".split("_"),
    longDateFormat: {
      LT: "HH:mm",
      LTS: "HH:mm:ss",
      L: "DD/MM/YYYY",
      LL: "D MMMM YYYY",
      LLL: "D MMMM YYYY HH:mm",
      LLLL: "dddd D MMMM YYYY HH:mm"
    },
    calendar: {
      sameDay: "[Anio amin'ny] LT",
      nextDay: "[Rahampitso amin'ny] LT",
      nextWeek: "dddd [amin'ny] LT",
      lastDay: "[Omaly amin'ny] LT",
      lastWeek: "dddd [lasa teo amin'ny] LT",
      sameElse: "L"
    },
    relativeTime: {
      future: "afaka %s",
      past: "%s lasa izay",
      s: "segondra vitsy",
      ss: "segondra %d",
      m: "minitra iray",
      mm: "minitra %d",
      h: "adiny iray",
      hh: "ora %d",
      d: "andro iray",
      dd: "andro %d",
      M: "volana iray",
      MM: "volana %d",
      y: "taona iray",
      yy: "taona %d"
    },
    week: { dow: 1, doy: 4 }
  });
  moment.locale(current);
})();
