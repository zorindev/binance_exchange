/**
 * 
 */

$(document).ready(function(){
	
	
	var updater = {
			
		socket: null,
		
		connect: function() {
			
			console.log("connecting ....");
			var url = "ws://" + location.host + "/websocket";
	        updater.socket = new WebSocket(url);
	        updater.socket.onmessage = function(event) {
	        	
	        	console.log(" message ", JSON.parse(event.data) );
	            updater.update(JSON.parse(event.data));
	        }
		},
		
		update: function(data) {
			
			var bll = (eval(data.BLL)).filter(function(entry){ return entry > 0; });
			var blu = (eval(data.BLU)).filter(function(entry){ return entry > 0; });
			
			bll.sort();
			blu.sort();
			
			var bol_chart_limit_low = bll[0] / 1.01;
			var bol_chart_limit_high = blu[blu.length - 1] * 1.01;
			
			console.log("bll: ", bll, "blu: ", blu);
			console.log("bll[last]: ", bll[bll.length - 1]);
			console.log("blu[0]: ", blu[0]);
			
			console.log("chart low: ", bol_chart_limit_low);
			console.log("chart high: ", bol_chart_limit_high);
			console.log("chart low enh: ", (bol_chart_limit_low / 1.01));
			console.log("chart high enh: ", (bol_chart_limit_high * 1.01));
				
			var boll = {
				x: eval(data.open_time),
				y: eval(data.BLL).filter(function(entry){ return entry > 0;} )
			};
			
			var close = {
				x: eval(data.open_time),
				y: eval(data.close).filter(function(entry){ return entry > 0;} )
			};
			
			var bolu = {
				x: eval(data.open_time),
				y: eval(data.BLU).filter(function(entry){ return entry > 0;} )
			};
			
			var signal_dates = eval(data.signal_date).filter(function(entry){ return (entry != null && entry.length > 0); } );
			var signals = eval(data.signal).filter(function(entry){ return entry > 0;} );
			
			var state = eval(data.state);
			
			console.log(data.state, state, typeof state)
			
			var signal_color = "black";
			if(state == 0){
				signal_color = "red";
			} else if(state == 2) {
				signal_color = "green";
			}
			
			console.log("signal_dates: ", signal_dates);
			console.log("signals: ", signals);
			
			var signal = {
				x: signal_dates,
				y: signals,
				type: 'scatter',
				mode: 'markers',
				marker: {
					color: signal_color,
					size: 3,
					line: {
						color: signal_color,
						width: 2
					}
				}
			};
			
			var layout = {
				title: 'Bollinger Range',
				
				xaxis: {
					autorange: false,
					type: 'date'
				},
				
				yaxis: {
					autorange: false,
					range: [bol_chart_limit_low, bol_chart_limit_high],
					//range: [0.0037, 0.0038],
					type: 'linear'
				},
				
			};
			
			var boll_plot = Plotly.newPlot('price', [boll, close, bolu, signal]);
			
			var k = {
				x: eval(data.open_time),
				y: eval(data.K),//.filter(function(entry){ return entry > 0;}),
				type: "scatter"
			};
			
			var d = {
				x: eval(data.open_time),
				y: eval(data.D),//.filter(function(entry){ return entry > 0;}),
				type: "scatter"
			};
			
			Plotly.newPlot('stochastic', [k, d]);
			
			$(".json_log").html("<pre>" + JSON.stringify(data, null, 4) + "</pre>");
		}
	}
	
	
	updater.connect();
	updater.socket.onopen = function (event) {
		
		$("#btn_start").on("click", function() {
			
			var number_of_periods = $("input#input_number_of_periods").val();
			var period = $("input#input_period_type").val();
			var rolling_window = $("input#input_rolling_window").val();
			
			try {
				
				number_of_periods = parseInt(number_of_periods);
				rolling_window = parseInt(rolling_window);
				var msg = {
					action: "start",
					exchange_client_name: "binance", 
		            api_key: "<enter_your_api_key>", 
		            api_secret: "<enter_your_api_secret>",
		            number_of_periods: number_of_periods,
		            period: period,
		            rolling_window: rolling_window
				};
				updater.socket.send(JSON.stringify(msg));
				
			} catch(err) {
				
				console.log(err);
			}
			
			 
		});
		
		
		$("#btn_stop").on("click", function() {
			var msg = {
				action: "stop",
			};
			updater.socket.send(JSON.stringify(msg)); 
		});
	};

	
});