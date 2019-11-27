<script>
var t_script = {{transcription | tojson}}.results.channel_labels.channels
var AddSpeaker = function (channel) {
		for (item in channel.items) {
			channel.items[item].channel_labels = channel.channel_labels
		}
}
var combined_tscript = t_script.map(AddSpeaker)

var app = new Vue({
  el: '#transcriptionApp',
  data: {
		transcription: combined_tscript
  },
	delimiters: ['{^', '^}']
})
</script>
