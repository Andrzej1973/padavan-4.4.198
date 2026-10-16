function wrVPNHandshakeText(o, labels) {
 if (!o || (o.state !== 1 && o.state !== 2)) return labels[0];
 if (o.observer !== 1 && o.observer !== 2) return labels[0];
 var fields = ['sample_age', 'peers', 'never', 'recent', 'old', 'future', 'youngest_age'];
 for (var i = 0; i < fields.length; i++) {
  var n = o[fields[i]];
  if (typeof n !== 'number' || !isFinite(n) || n < 0 || Math.floor(n) !== n || n > 9007199254740991) return labels[0];
 }
 if (o.peers > 128 || o.never + o.recent + o.old + o.future !== o.peers || (o.has_age !== 0 && o.has_age !== 1)) return labels[0];
 return (o.state === 2 ? labels[1] + '. ' : '') + labels[10] + ': ' +
  (o.observer === 1 ? 'WireGuard' : 'AmneziaWG') + '; ' + labels[2] + ': ' + o.peers +
  '; ' + labels[3] + ': ' + o.recent + '; ' + labels[4] + ': ' + o.never +
  '; ' + labels[5] + ': ' + o.old + '; ' + labels[6] + ': ' + o.future +
  '; ' + labels[7] + ': ' + o.sample_age + ' ' + labels[9] +
  (o.has_age ? '; ' + labels[8] + ': ' + (o.youngest_age + o.sample_age) + ' ' + labels[9] : '');
}
if (typeof module !== 'undefined') module.exports = wrVPNHandshakeText;
