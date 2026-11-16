/* Runs functions of site/logic.js for the Python tests. Reads a JSON list of calls [name, arg, ...]
   from stdin and writes the list of results. {"$date": "..."} becomes a Date. */
"use strict";
var logic = require("../../site/logic.js");

function revive(value) {
  if (Array.isArray(value)) return value.map(revive);
  if (value && typeof value === "object") {
    if (typeof value.$date === "string") return new Date(value.$date);
    Object.keys(value).forEach(function (key) { value[key] = revive(value[key]); });
  }
  return value;
}

var input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", function (chunk) { input += chunk; });
process.stdin.on("end", function () {
  var results = JSON.parse(input).map(function (call) {
    var value = logic[call[0]];
    return typeof value === "function" ? value.apply(null, revive(call.slice(1))) : value;
  });
  process.stdout.write(JSON.stringify(results));
});
