/**
 * 
 */


var FOUR_DISPLAY_DIGITS 	= 4;
var MAX_DISPLAY_DIGITS 	= 8;

$(document).ready(function(){
	
	var enable_transactions = false;
	var enable_live_data = false;
	
	var enable_bollinger_signal_eval = true;
	var enable_stochrsi_signal_eval = true;
	var enable_sma_signal_eval = false;
	

	
	$("#enable_bollinger").click();
	$("#enable_stoch_rsi").click();
	
	
	// cycle display //
	var prev_cycle_profit = 0.0000;	
	var prev_cycle_duration = 0.0000;
	

	var prev_target_entry_price = 0.0000;
	var prev_target_units_bought = 0.0000;
	var prev_target_profit_price = 0.0000;
	var prev_target_units_sold = 0.0000;
	
	var prev_buy_fee = 0.0000;
	var prev_sell_fee = 0.0000;
	
	var prev_cycle = 0;
	
	
	function get_chart_range(data, low_key, high_key) {
		
		var rtn = [];
		
		if(low_key in data && high_key in data) {
			var low_values = (eval(data[low_key]));
			var high_values = (eval(data[high_key]));
			
			low_values.sort();
			high_values.sort();
			
			var low = low_values[0];
			var high = high_values[high_values - 1] * 1.01;
			
			rtn = [low, high];
		}
		
		return rtn;
	}
	
	var updater = {
			
		socket: null,
		
		connect: function() {
			
			console.log("connecting ....");
			var url = "ws://" + location.host + "/websocket";
	        updater.socket = new WebSocket(url);
	        
	        updater.socket.onmessage = function(event) {	
	        	console.log(" message ", JSON.parse(event.data) );
	            updater.update(JSON.parse(event.data));
	        };    
		},
		
		onConnectEvent: function() {
			console.log(updater.socket.readyState);
			
			updater.socket.onopen = function() {
			    console.log('onopen called');
			};
			
			var msg = {
	        	action: "status",
	        };
	        updater.socket.send(JSON.stringify(msg));	
		},
		
		update: function(data) {
			
			console.log(" data that was sent back ....");
			
			console.log(" *** DEBUG *** ");
			console.log(data);
			console.log(" *** DEBUG *** ");
			
			if(data.hasOwnProperty("status")) {
					
				console.log("handling status ")
				var engine_status = data.status;
				
				console.log(engine_status);
				
				if(engine_status === "not_initialized") {
					console.log("not initialized");
					
				} else if(engine_status === "not_running") {
					console.log("not running");
					
				} else if(engine_status === "running") {
					console.log("running. reconnecting ui ... ");
					
					var msg = {
			        	action: "reconnect",
			        };
			        updater.socket.send(JSON.stringify(msg));
			        
			        console.log("sent reconnect");
					
				} else if(engine_status === "stopped") {
					console.log("stopped")
					
				}
				
				return;
				
			} else {
				
				debugger;
				console.log("otherwise handle data ... ");
				console.log(data);
				
				if(data.ERROR.length > 0) {
					$("#pre_error_content").text(data.ERROR.replace(/\r\n/g,'\n'));
					$("#error_cntr").show();
				}
					
				var bollinger_price_range = get_chart_range(data, "BLLC", "BLUC");
				var price_width_range = get_chart_range(data, "PRICE_WIDTH", "PRICE_WIDTH");
				var ema_8_13_diff_range = get_chart_range(data, "EMA_8_13_DIFF", "EMA_8_13_DIFF")
				
				
				// signal data setup
				var buy_signal_dates = eval(data.buy_signal_date);//.filter(function(entry){ return (entry != null && entry.length > 0); } );
				
				var buy_signals = eval(data.buy_signal);//.filter(function(entry){ return entry > 0;} );
				
				var sell_signal_dates = eval(data.sell_signal_date);
				
				var sell_signals = eval(data.sell_signal);
				
				var state = eval(data.state);
				
				var buy_signal_color = "green";
				var sell_signal_color = "red";
				var up_trend_color = "green";
				var down_trend_color = "red";
				
				
				var candlestick = {
					x: eval(data.open_time),
					open: eval(data.open),
					close: eval(data.close),
					low: eval(data.low),
					high: eval(data.high),
					increasing: {line: {color: '#17BECF'}},
					decreasing: {line: {color: '#7F7F7F'}}, 
					line: {color: 'rgba(31,119,180,1)'},
					type: 'candlestick',
					xaxis: 'x',
					yaxis: 'y',
					name: "OCLH",
				};
				
				
				// bollinger trace
				var boll = {
					x: eval(data.open_time),
					
					y: eval(data.BLLC),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y',
					name: 'Boll Band Low'
				};
				
				var bolm = {
					x: eval(data.open_time),
					
					y: eval(data.BLMC),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y',
					
					name: 'Boll Band Mid'
				};
				
				var bolu = {
					x: eval(data.open_time),
					
					y: eval(data.BLUC),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y',
					name: 'Boll Band High'
				};
				
				var sma7 = {
					x: eval(data.open_time),
					
					y: eval(data.PRICE_SMA_7),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'PRICE SMA 7'
				}
				
				var sma25 = {
					x: eval(data.open_time),
					
					y: eval(data.PRICE_SMA_25),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'PRICE SMA 25'
				}
				
				var sma_ctrl = {
					x: eval(data.open_time),
					
					y: eval(data.PRICE_SMA_CTRL),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'Controling SMA price'
				}
				
				
				var ema_8 = {
					x: eval(data.open_time),
					
					y: eval(data.EMA_8),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'EMA 8',
					
					line: {
						color: "blue"
					}
				}
				
				var ema_13 = {
					x: eval(data.open_time),
					
					y: eval(data.EMA_13),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'EMA 13',
					
					line: {
						color: "green"
					}
				}
				
				var ema_21 = {
					x: eval(data.open_time),
					
					y: eval(data.EMA_21),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'EMA 21',
					
					line: {
						color: "yellow"
					}
				}
				
				var ema_55 = {
					x: eval(data.open_time),
					
					y: eval(data.EMA_55),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y3',
					name: 'EMA 55',
					
					line: {
						color: "red"
					}
				}
				
				var ema_8_13_diff = {
					x: eval(data.open_time),
					
					y: eval(data.EMA_8_13_DIFF),//.filter(function(entry){ return entry > 0;} ),
					
					xaxis: 'x',
					yaxis: 'y2',
					name: 'EMA DIFF',
					
					line: {
						color: "black"
					}
				}
				
				var stoch_rsi_k = {
					x: eval(data.open_time),
					
					y: eval(data.STOCH_RSI_K),
					
					xaxis: 'x',
					yaxis: 'y2',
					name: 'Stoch RSI K'
				}
				
				var stoch_rsi_d = {
					x: eval(data.open_time),
					
					y: eval(data.STOCH_RSI_D),
					
					xaxis: 'x',
					yaxis: 'y2',
					name: 'Stoch RSI D'
				}
				
				// buy signal
				var buy_signal_scatter = {
					x: buy_signal_dates,
					y: buy_signals,
					type: 'scatter',
					name: 'buy signal',
					mode: 'markers',
					marker: {
						color: buy_signal_color,
						size: 3,
						line: {
							color: buy_signal_color,
							width: 2
						}
					},
					xaxis: 'x',
					yaxis: 'y',
				};
				
				// sell signal
				var sell_signal_scatter = {
					x: sell_signal_dates,
					y: sell_signals,
					type: 'scatter',
					name: 'sell signal',
					mode: 'markers',
					marker: {
						color: sell_signal_color,
						size: 3,
						line: {
							color: sell_signal_color,
							width: 2
						}
					},
					xaxis: 'x',
					yaxis: 'y',
				};
				
				// layout setup
				var plot_data = [
					
					candlestick,
					
					boll, 
					bolm, 
					bolu, 

					buy_signal_scatter, 
					sell_signal_scatter,
					
					//stoch_rsi_k,
					//stoch_rsi_d,
					
					ema_8,
					ema_13,
					ema_21,
					ema_55,
					
					
					ema_8_13_diff,


				];
				
				var layout = {
					title: 'Market Evaluation',
					
					showlegend: true,
					hovermode: 'x',
					
					xaxis: {
						type: 'date',
						
						showspikes: true,
						spikemode: 'across',
						spikesnap: 'cursor',
						showline: true,
						showgrid: true,
					},
					
					yaxis: {
						domain: [0.67, 1],
						range: [bollinger_price_range[0], bollinger_price_range[1]],
						type: 'linear',
					},
						
					yaxis2: {
						domain: [0.34, 0.66],
						range: [ema_8_13_diff_range[0], ema_8_13_diff_range[1]],//[0.0, 1.0], 
						type: 'linear',
					},
					
					yaxis3: {
						domain: [0.00, 0.33],
						range: [bollinger_price_range[0], bollinger_price_range[1]],
						type: 'linear',
					},
					
					autosize: false,
					width: 5000,
					height: 5000,
					
				};
				Plotly.newPlot('plot_cntr_boll', plot_data, layout);
				
				$(".json_log_cntr").html("<pre>" + JSON.stringify(data, null, 4) + "</pre>");
				
				var cycle_profit = parseFloat(data.CYCLE_PROFIT.toFixed(MAX_DISPLAY_DIGITS));
				prev_cycle_duration = parseFloat(data.CYCLE_DURATION.toFixed(FOUR_DISPLAY_DIGITS));
				prev_target_entry_price = parseFloat(data.TARGET_ENTRY_PRICE.toFixed(MAX_DISPLAY_DIGITS));
				prev_target_profit_price = parseFloat(data.EXIT_PRICE.toFixed(MAX_DISPLAY_DIGITS));
				prev_target_units_bought = parseFloat(data.TARGET_UNITS_BOUGHT.toFixed(MAX_DISPLAY_DIGITS));
				
				prev_buy_fee = parseFloat(data.BUY_FEE.toFixed(MAX_DISPLAY_DIGITS));
				prev_sell_fee = parseFloat(data.SELL_FEE.toFixed(MAX_DISPLAY_DIGITS));
				
				var prev_buy_fee_currency = data.BUY_FEE_CURRENCY;
				var prev_sell_fee_currency = data.SELL_FEE_CURRENCY;

				$("#stats_cycle_profit").text(cycle_profit);

				//if(prev_cycle_duration != 0) {
					$("#stats_cycle_duration").text(prev_cycle_duration);
				//}
				
				//if(prev_target_entry_price != 0) {
					$("#stats_target_entry_price").text(prev_target_entry_price);
				//} 
				
				//if(prev_target_entry_price != 0) {
					$("#stats_target_units_bought").text(prev_target_units_bought);
				//}
				
				//if(prev_target_profit_price != 0) {
					$("#stats_target_profit_price").text(prev_target_profit_price);
				//}
				
				//if(prev_target_profit_price != 0) {
					$("#stats_buy_fee").text(prev_buy_fee + " " + prev_buy_fee_currency);
				//}
				
				//if(prev_target_profit_price != 0) {
					$("#stats_sell_fee").text(prev_sell_fee + " " + prev_sell_fee_currency);
				//}
				
				// total stats
				///$("#stats_profit").text(data.PROFIT.toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_avg_cycle_duration").text(data.AVG_TRADE_DURATION.toFixed(FOUR_DISPLAY_DIGITS));
				$("#stats_avg_gain").text(data.AVG_GAIN.toFixed(MAX_DISPLAY_DIGITS));
					
				$("#stats_cycle_count").text(data.CYCLE_COUNT);
				$("#stats_total_duration").text(data.TOTAL_CYCLE_TIME);
				$("#stats_average_purchase_price").text(data.AVG_ENTRY_PRICE.toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_average_units_bought").text(data.AVG_UNITS_BOUGHT.toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_average_sale_price").text(data.AVG_EXIT_PRICE.toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_sma_delta").text(data.PRICE_SMA_CTRL_DELTA_SUM.toFixed(MAX_DISPLAY_DIGITS));
				
			
				$("#stats_current_close").text(  eval(data.close)[eval(data.close).length - 1].toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_boll_low").text(  eval(data.BLLC)[eval(data.BLLC).length - 1]  .toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_stoch_k").text(  eval(data.STOCH_RSI_K)[eval(data.STOCH_RSI_K).length - 1]  .toFixed(MAX_DISPLAY_DIGITS));
				$("#stats_stoch_d").text(  eval(data.STOCH_RSI_D)[eval(data.STOCH_RSI_D).length - 1]  .toFixed(MAX_DISPLAY_DIGITS));
			}
		}
	}
	
	updater.connect();
	updater.socket.onopen = function (event) {
		console.log(updater.socket.readyState);
		
		updater.socket.onopen = function() {
		    console.log('onopen called');
		};
		
		var msg = {
        	action: "status",
        };
        updater.socket.send(JSON.stringify(msg));
        
		$("#btn_start").on("click", function() {
			
			var market 					=   $("select#input_market_select option:selected").val();
			var starting_amount 		=   $("#input_starting_amount").val();
			
			var number_of_periods 		=	$("input#input_number_of_periods").val();
			var period_type				= 	$("select#input_period_select_type option:selected").val();
			var boll_rolling_window 	= 	$("input#input_bollinger_rolling_window").val();
			var signal_threshold 		= 	$("input#input_threshold").val();
			
			
			var rsi_period 				=   $("#rsi_period").val();
			var stoch_period 			=   $("#stoch_period").val();
			var smooth_k				=   $("#smooth_k").val();
			var smooth_d				=   $("#smooth_d").val();
			var rsi_entry_limit			=   $("#stoch_rsi_entry_level").val();
			var rsi_exit_limit			=   $("#stoch_rsi_exit_level").val();
			
			
			var ctrl_sma_limit			=   $("#input_ctrl_sma_window").val();
			var static_df_period		=	$("#static_df_period").val();
			
			
			
			try {
				number_of_periods = parseInt(number_of_periods);
				boll_rolling_window = parseInt(boll_rolling_window);
				signal_threshold = parseFloat(signal_threshold);
				
				var msg = {
					
					// action
					action: "start",
						
					// new automation key
					api_key: "", 
					api_secret: "",
						
					// market
					exchange_client_name: "binance",
					market_code: market,
					starting_amnt: starting_amount,
					
					// bollinger
		            number_of_periods: number_of_periods,
		            period_type: period_type,
		            boll_rolling_window: boll_rolling_window,
		            signal_thresh: signal_threshold,
		            
		            // rsi
		            rsi_period_: rsi_period,
					stoch_period_: stoch_period,
					smooth_k_: smooth_k,
					smooth_d_: smooth_d,
					rsi_entry_limit_: rsi_entry_limit,
					rsi_exit_limit_: rsi_exit_limit,
		            
		            // sma
		            ctrl_sma_limit_: ctrl_sma_limit,
		            
		            // controls
		            enable_boll: enable_bollinger_signal_eval,
		            enable_stochrsi: enable_stochrsi_signal_eval,
		            enable_sma: enable_sma_signal_eval,
		            enable_lvdt: enable_live_data,
		            enable_trxs: enable_transactions,
		            static_df_period_: static_df_period
		            
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
		
		
		$("#enable_bollinger").on("change", function(){
			
			
			if(!enable_bollinger_signal_eval) {
				enable_bollinger_signal_eval = true;
			} else {
				enable_bollinger_signal_eval = false;
			}
		});
		
		$("#enable_stoch_rsi").on("change", function(){
			
			if(!enable_stochrsi_signal_eval) {
				enable_stochrsi_signal_eval = true;
			} else {
				enable_stochrsi_signal_eval = false;
			}
		});
		
		$("#enable_sma").on("change", function(){
			
			if(!enable_sma_signal_eval) {
				enable_sma_signal_eval = true;
			} else {
				enable_sma_signal_eval = false;
			}
		});
		
		$("#enable_live_data").on("change", function() {
			if(!enable_live_data) {
				enable_live_data = true;
				$("#enable_transactions").prop("disabled", false); 
				$("#static_df_period_cntr").hide();
				$("#static_df_period").val("")
			} else {
				enable_live_data = false;
				$("#enable_transactions").prop("disabled", true);
				$("#static_df_period_cntr").show();
				$("#static_df_period").val("YYYY/MM/DD");
			}
		});
		
		$("#enable_transactions").on("click", function() {
			if(!enable_transactions) {
				enable_transactions = true;
			} else {
				enable_transactions = false;
			}
		});
	};
});