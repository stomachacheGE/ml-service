
 $(document).ready(function () {

 	 $('[data-tooltip="tooltip"]').tooltip();
 	 var access_key = $('#access-key').data('key');

 	 //jump to another model
 	 $('#current-page-model').change(function () {
 	 	jump_to_model = $('#current-page-model option:selected').text();
 	 	 $('#overview-li').click();
 	 });

 	 //this function is used when jump to different section of the model
 	function jump_to(location, callback) {
 		var model = $('#current-page-model option:selected').text();
 		$.ajax({
          type: "GET",
          url: "http://"+document.location.host+"/model?name="+model+"&to="+location,
          //cache: false,
          success: function (data) {
            $('.main').html(data)
            console.log('ajax')
          },
          error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
          },  
          complete: function() {
             callback()
          }
        });
 	}

  //Save Real time score hint
    $(document).on('click', '#save-hint', function () {
      $('#save-hint').addClass('button--disabled');
      $('#save-hint').html('Saving...'); 
      var modelsname = $('#current-page-model option:selected').text();
      $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+modelsname+"/hint?access_key="+access_key,
          data: JSON.stringify({"hint": $("textarea#hint-text").val()}),
          success: function() {
              $('#real-time-score-hint').modal('hide')
          },
          error: function (jqXHR, status) {
            alert(jqXHR.responseText);
          }, 
          complete: function () {
          $("#save-hint").html('Save Change'); 
          $('#save-hint').removeClass('button--disabled');
          } 
        });
    });
    
  //Save Model Description
    $(document).on('click', '#save-description', function () {
      $('#save-description').addClass('button--disabled');
      $('#save-description').html('Saving...'); 
      var modelsname = $('#current-page-model option:selected').text();
      $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+modelsname+"/description?access_key="+access_key,
          data: JSON.stringify({"description": $("textarea#description-text").val()}),
          error: function (jqXHR, status) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
          }, 
          complete: function () {
          $("#save-description").html('Save Change'); 
          $('#save-description').removeClass('button--disabled');
          } 
        });
    });

	//Metadata Section
 	$('#metadata-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 			$('#input-metadata-table').dynatable({
			    features: {
			        pushState: false,
			        search: false,
			    },        
			    table: {
			        defaultColumnIdStyle: 'camelCase'
			    },
			    dataset: {
			        perPageDefault: 5,
			        perPageOptions: [5,10,20],
			    },
			});
			$('#output-metadata-table').dynatable({
			    features: {
			        pushState: false,
			        search: false,
			    },        
			    table: {
			        defaultColumnIdStyle: 'camelCase'
			    },
			    dataset: {
			        perPageDefault: 5,
			        perPageOptions: [5,10,20],
			    },
			});
			console.log('test')
 		});
 	});
 	// Overview Section
 	 $('#overview-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
			console.log('test')
 		});
 	});

 	// Score Section
    var score_step;
    var score_type;

 	$('#score-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 			score_step = 1;
 		});
 	});

 	$(document).on('click', '#choose-batch', function () {
 		$('#score-last').show();
 		$('#score-next').show();
 		$(this).hide();
 		$(this).siblings('#choose-real-time').hide();
 		score_type = "batch";
 		$('.'+score_type+'_step_'+score_step).show();
 		$('#batch-score-input-wrapper').show();
 		$('#choose-table-alert').show();
 		$('#choose-type-alert').hide();
 		//$('.score-table-area').show();
 		console.log(score_type+score_step)
 		console.log(score_step)
 	});

 	$(document).on('click', '#choose-real-time', function () {
 		$('#score-last').show();
 		$('#score-next').show();
 		$(this).hide();
 		$(this).siblings('#choose-batch').hide();
 		score_type = "real_time";
 		$('.'+score_type+'_step_'+score_step).show();
 		$('#real-time-score-input-wrapper').show();
 		$('#batch-score-input-wrapper').hide();
 		$('#real-time-score-input').show();
 	});

 	$(document).on('click', '#score-next', function () {
 		$('.'+score_type+'_step_'+score_step).hide();
 		score_step += 1;
 		$('.'+score_type+'_step_'+score_step).show();
 		$(this).hide();
 		console.log('#'+score_type+'_step_'+score_step)
 	});

 	$(document).on('click', '#score-last', function () {
 		$('.'+score_type+'_step_'+score_step).hide();
 		if (score_step != 1) {
 			score_step -= 1;
 			$('#score-next').show();
 			$('.'+score_type+'_step_'+score_step).show();
 			$('#score-output-wrapper').hide();
 			var score_minus_type = score_type.replace("_", "-");
 			console.log(score_minus_type);
 			$('#'+score_minus_type+'-score-input-wrapper').show();
 			console.log('#'+score_type+'_step_'+score_step)
 		}
 		else {
 			$('#choose-batch').show();
 			$('#choose-real-time').show();
 			$('.score-last-next').hide();
 			$('#real-time-score-input-wrapper').hide();
 			$('#real-time-score-input').hide();
 			$('#batch-score-input-wrapper').hide();
 			$('#choose-table-alert').hide();
 			$('#choose-type-alert').show();
 		}
 	});
 	//actions for real-time-score
 	$(document).on('click', '#add-entry', function () {
        var new_row = $(".current-row").clone();
        console.log(new_row)
        $(".input-row").removeClass("current-row");
        $('#real-time-score-input tr:last').after(new_row);
        $(".current-row td input").val("");
    });
    
    $(document).on('click', '#delete-entry', function () {
        $(".current-row").remove();
        $("#real-time-score-input tr:last").addClass("current-row");
    });

    $(document).on('click', '#score-get-hint', function () {
    	var modelsname = $('#current-page-model option:selected').text();
    	$('#real-time-score-hint').remove();
       	$.ajax({
	      type: "GET",
	      url: "http://"+document.location.host+"/api/"+modelsname+"/hint?response_type=html&access_key="+access_key,
	      success: function(data){
	      	$('#error-modal').after(data);
    			var modal = $('#real-time-score-hint');
    			modal.modal('show');
	      }
	    });
    });
/*
    $('#save-hint').click(function () {
      $('#new-test').modal('hide');
      $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+get_url_type(type)+"/models/"+modelsname+"/hint",
          data: JSON.stringify({"value": $("textarea#hint-text").val()}),
          success: function (data) {
              console.log('success');
          },
          error: function (jqXHR, status) {
            alert("Sorry, there was a problem when saving hint!");
          },  
        });
    }); */

    //generate batch score table list
    $(document).on('change', '#choose-batch-score-schema', function () {
    	$("#choose-batch-score-table option:not(:first-child)").remove();
    	var selected_schema = $("#choose-batch-score-schema option:selected" ).text();
    	var url;
    	if (selected_schema == 'Samples') {
    		url = "http://"+document.location.host+"/tables?sample=true&access_key="+access_key
     	}
     	else {
     		url = "http://"+document.location.host+"/tables?sample=false&access_key="+access_key
     	}

	    $.ajax({
	      type: "GET",
	      url: url,
	      success: function (data) {
	        $("#choose-batch-score-table option:first").after(data);
	        batch_score_primary_key_autofill();
	        },
        error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
           }
	    });

    });

    $(document).on('change', '#choose-batch-score-table', function () {
    	$("#choose-batch-score-primary-key option:not(:first-child)").remove();
    	var selected_table = $("#choose-batch-score-table option:selected" ).text();
	    $.ajax({
	      type: "GET",
	      url: "http://"+document.location.host+"/columns?table="+selected_table+"&access_key="+access_key,
	      success: function (data) {
	        $("#choose-batch-score-primary-key option:first").after(data);
	        },
        error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            }
	    });

    });
    
    function batch_score_primary_key_autofill () {
    	$("#choose-batch-score-primary-key option:not(:first-child)").remove();
        var table = $("#choose-batch-score-table option:nth-child(2)").val();
        console.log(table);
        $.ajax({
          type: "GET",
          url: "http://"+document.location.host+"/columns?table="+table+"&access_key="+access_key,
          success: function (data) {
            $("#choose-batch-score-primary-key option:first").after(data);
           },
          error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            }
        });  
    }
    
    //dynamically display table when scoring
     $(document).on('change', '#choose-batch-score-table', function () {
     	//$('#batch-score-input-wrapper').html('');
       var table_name =$("#choose-batch-score-table option:selected" ).text();
       console.log(table_name);
       var table = '<div class="score-table-area"><table class="score-table" id="batch-score-input" hidden><thead><tr></tr></thead><tbody><tr></tr></tbody></table></div>'
       $('#batch-score-input-wrapper').html(table);
       
	   $.ajax({
	       type: "GET",
	       url: "http://"+document.location.host+"/columns?table="+table_name+"&header=true&access_key="+access_key,
	       success: function(data){
	            $('#batch-score-input thead tr').html(data);
	       },
        error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            },
	       complete: function(jqXHR, textStatus) {
	          if (textStatus == 'success') {
	            var dynatable = $('#batch-score-input').dynatable({
	                features: {
	                    pushState: false,
	                    search: false,
	                },        
	                table: {
	                    defaultColumnIdStyle: 'lowercase'
	                },
	                dataset: {
	                    perPageDefault: 10,
	                    perPageOptions: [5,10,20],
	                },
	            }).data('dynatable');

	            $.ajax({
	                type: "GET",
	                url: "http://"+document.location.host+"/tables?table="+table_name+"&access_key="+access_key,
	                success: function(data){
	                    dynatable.records.updateFromJson({records: data});
	                    dynatable.records.init();
	                    dynatable.process();
	                    $('#batch-score-input-wrapper').show()
	                    $('#batch-score-input').show()
	                },
                  error: function(jqXHR) {
                var modal = $('#error-modal');
                $('#error-modal-message').html(jqXHR.responseText);
                modal.modal('show')
              }
	            });   
	          }
	       }
	    });  
	});

	//real-time-score 
	$(document).on("click", "#real_time_score", function () {
		$('#real_time_score').html('Scoring...');
		$('#real_time_score').addClass('operating');
    	var modelsname = $('#current-page-model option:selected').text();
    	$("#score-output-wrapper").hide();
    	$("#score-output-wrapper").html("");
        var inputnames = [];
        $('#real-time-score-input').find(".input-name").each(function () {
            inputnames.push($(this).html());
        });
        
        var multi_line_values = {};
        for (i = 0; i < inputnames.length; i++) {
            var input = inputnames[i]; 
            var values = validated_input("."+input);  
            multi_line_values[inputnames[i]] = values;
        };
        console.log(multi_line_values);
        $.ajax({
            type:"POST",
            url: "http://"+document.location.host+"/api/"+modelsname+"/real_time_score?response_type=html&access_key="+access_key,
            contentType:"application/json; charset=utf-8",
            data: JSON.stringify(multi_line_values),
            success:function (data) {
            	$('#real-time-score-input-wrapper').hide();
                $("#score-output-wrapper").html(data);
                $('#score-output-table').dynatable({
			        features: {
			        	  search: false,
			              pushState: false,
			        },
			        table: {
			          defaultColumnIdStyle: 'underscore'
			        },
			        dataset: {
			          perPageDefault: 10,
			        },
			      })
            },
            error: function (jqXHR) {
            	$('#real_time_score').html('Score Now');
		          $('#real_time_score').removeClass('operating');
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            },
            complete: function () {
                $('#score-output-wrapper').show();
                $('#real_time_score').html('Score Now');
		            $('#real_time_score').removeClass('operating');
            }
        });
    });

	//batch score
	$(document).on("click", "#batch_score",function () {
        $('#batch_score').html('Scoring...');
		$('#batch_score').addClass('operating');
    	var modelsname = $('#current-page-model option:selected').text();
    	$("#score-output-wrapper").hide();
    	$("#score-output-wrapper").html("");
    	selected_schema = $('#choose-batch-score-schema').val();
    	var input_table;
    	if (selected_schema == 'Samples') {
	    	input_table = 'SAMPLES.'+$('#choose-batch-score-table').val();
	    }
	    else {
	    	input_table = $('#choose-batch-score-table').val();	
	    }
        var model_data = {
            "input_table" :  input_table,
            "primary_key" :  $("#choose-batch-score-primary-key").val()
        }
        
        if ($("#custom_table_name").val()) {
            model_data.table_name = $("#custom_table_name").val().replace(/ /g,"_");
        }
        
        console.log(model_data)
        
        $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+modelsname+"/batch_score?response_type=html&access_key="+access_key,
          data: JSON.stringify(model_data),
	        success:function (data) {
	        	$('#batch-score-input-wrapper').hide();
	            $("#score-output-wrapper").html(data);
	            $('#score-output-table').dynatable({
			        features: {
			        	  search: false,
			              pushState: false,
			        },
			        table: {
			          defaultColumnIdStyle: 'underscore'
			        },
			        dataset: {
			          perPageDefault: 10,
			        },
			      })
	        },
	        error: function (jqXHR) {
	        	$('#batch_score').html('Score Now');
		        $('#batch_score').removeClass('operating');
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
	        },
	        complete: function () {
	            $('#score-output-wrapper').show();
	            $('#batch_score').html('Score Now');
		        $('#batch_score').removeClass('operating');
	        }
        });
    });

	// History Section
	$('#history-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 		});
 	});

 	//dynamically display history table 
     $(document).on('click', '#retrieve', function () {
     	//$('#batch-score-input-wrapper').html('');
      $('#retrieve').html('Retrieving...');
      $('#retrieve').addClass('operating');
     	var type = $("#hist-type-select").val();
        var sort = $("#hist-sort-select").val();
        var modelsname = $('#current-page-model option:selected').text();
        if (type=="all") {
            url = "http://"+document.location.host+"/api/"+modelsname+"/history?sort="+sort+"&access_key="+access_key;
        }
        else {
            url = "http://"+document.location.host+"/api/"+modelsname+"/history?type="+type+"&sort="+sort+"&access_key="+access_key;
        }
       
       function row_writer_1(rowIndex, record, columns, cellWriter) {
       var row;
       if (record.behaviour == 'score') {
       		row = '<tr><td>'+record.behaviour+'</td><td>'+record.creation_time+'</td><td> \
       		<button type="button" class="btn btn-default" data-score-type="'+record.value.scoretype+'" data-io="input" data-type="'+record.behaviour+'" data-time="'+record.creation_time+'" data-toggle="modal" data-tooltip="tooltip" data-placement="bottom" title="Show Input Table"> \
            <span class="glyphicon glyphicon-log-in" aria-hidden="true"></span></button> \
            <button type="button" class="btn btn-default" data-score-type="'+record.value.scoretype+'" data-io="output" data-type="'+record.behaviour+'" data-time="'+record.creation_time+'" data-toggle="modal" data-tooltip="tooltip" data-placement="bottom" title="Show Output Table" > \
            <span class="glyphicon glyphicon-log-out" aria-hidden="true"></span></button> \
            </td></tr>';
        }
        else if (record.behaviour == 'refresh') {
        	row = '<tr><td>'+record.behaviour+'</td><td>'+record.creation_time+'</td><td> \
       		<button type="button" class="btn btn-default" data-type="'+record.behaviour+'" data-io="else" data-time="'+record.creation_time+'" data-toggle="modal" data-tooltip="tooltip" data-placement="bottom" title="Show Source Table" >\
            <span class="glyphicon glyphicon-folder-close" aria-hidden="true"></span></button>\
            </td></tr>';
        }
        else {
        	row = '<tr><td>'+record.behaviour+'</td><td>'+record.creation_time+'</td><td>\
       		<button type="button" class="btn btn-default" data-type="'+record.behaviour+'" data-io="else" data-time="'+record.creation_time+'" data-toggle="modal" data-tooltip="tooltip" data-placement="bottom" title="Show Details" >\
            <span class="glyphicon glyphicon-align-justify" aria-hidden="true"></span></button>\
            </td></tr>';
        }
        return row;
    	}
    
	   var dynatable = $('#history-table').dynatable({
	        features: {
	        	  search: false,
	              pushState: false,
	        },
	        table: {
	          defaultColumnIdStyle: 'underscore'
	        },
	        dataset: {
	          perPageDefault: 10,
	        },
	        writers: {
	          _rowWriter: row_writer_1
	        }
	      }).data('dynatable');
	    
	    $.ajax({
	      type: "GET",
	      url: url,
	      success: function(data){
	          console.log(data);
	          dynatable.records.updateFromJson({records: data});
	          dynatable.records.init();
	          dynatable.process();
	          $('#history-table-wrapper').show();
	          $('#history-table').show()
	      },
        error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            },
        complete: function() {
          $('#retrieve').html('Retrieve Now');
          $('#retrieve').removeClass('operating');
        }
	    });
	});

	//show corresponding modal when user clicks the operation buttons in a history record row
	//the modal details are input/output table or refresh table or visualization details
	$(document).on('click', '#history-table button', function () {
		$('#show-table').remove();
		console.log('click');
		var model_name = $('#current-page-model option:selected').text();
		var hist_type = $(this).data('type');
		var hist_time = $(this).data('time');
		var io = $(this).data('io')
	    $.ajax({
	      type: "GET",
          url:"http://"+document.location.host+"/"+model_name+"/history/details?type="+hist_type+"&time="+hist_time+"&io="+io+"&access_key="+access_key,
	      success: function(data){
	      	$('#error-modal').after(data);
	          if (hist_type == 'score' || hist_type == 'refresh') {
		          $('#show-table').dynatable({
				    features: {
				        pushState: false,
				        search: false,
				        perPageSelect: false
				    },        
				    table: {
				        defaultColumnIdStyle: 'underscore'
				    },
				    dataset: {
				        perPageDefault: 10,
				    },
				  });
				  $('#show-table').wrap('<div id="show-table-wrapper"></div>');
	      }
	  	 },
      error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            },
	      complete: function(data) {
	      	var modal = $('#history-detail-modal');
			modal.modal('show');
	      }
	    });
	})


	//Refresh Model Section
	//This part is modified base on ADD NEW MODEL 
	$('#refresh-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 			$('.add-new-dashdb-step-2').show();
      		$('.add-new-spss-step-2').show();
 		});
 	});
	    
	   var step = 2; // the first step of adding new model is skipped, since now we are refreshing a model


	  $(document).on('click', '#add-next', function () {
	    $('#add-last').show();
	    $('.add-new-dashdb-step-'+step).hide();
	    step += 1;
	    $('.add-new-dashdb-step-'+step).show();
	    if (step==3) {
	      $(this).hide();          
	    }
	  });

	  $(document).on('click', '#add-last', function () {
	    $("#spss-choose-file-info").hide();
	    $('#add-next').show();
	    $('.add-new-dashdb-step-'+step).hide();
	      step -= 1;
	      $('.add-new-dashdb-step-'+step).show();
	      if (step == 2) {
	       $(this).hide();
	       $('#choose-dashdb-input-alert').hide();
	     }
	    });

	  $(document).on('change', "#choose-str-file-td input:file", function (){
	  	console.log('file selected')
	   var fileName = $(this).val().replace("C:\\fakepath\\", "");
	   //fileName.value.replace("C:\\fakepath\\", "");
	   $("#spss-choose-file-info .filename").html(fileName);
	   $("#spss-choose-file-info").fadeIn("slow");
	   $("#spss-choose-file-alert").hide()
	 });

  $(document).on('click','#add-new-spss-create-now', function(event) {
    console.log('submit');
    $('#add-new-spss-create-now').addClass('operating');
        $('#add-new-spss-create-now').html('Refreshing...');
        

      $('#upload-form').submit();
          
      });

$(document).on('submit', '#upload-form', function() {
        var model_name =  $('#current-page-model option:selected').text();
        // submit the form 
        $('#upload-form').ajaxSubmit({
            url: "http://"+document.location.host+"/api/"+model_name+"?response_type=html&access_key="+access_key,
              success: function (data) {
                $('#add-new-spss-create-now').html('Refresh Now');
                $('#error-modal').after(data);
              },
              error: function (jqXHR, status) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
                modal.modal('show')
                $('#add-new-spss-create-now').html('Refresh Now');
              },  
              complete: function () {
                var modal = $('#add-new-model-alert');
               modal.modal('show');
                $('#add-new-spss-create-now').removeClass('operating');
              }
            });
        
        return false;
});
	  //when click the table cell, it should trigger file input. THIS DOES NOT WORK
	  /*
	  $('#choose-str-file-td').click(function() {
	    $('#choose-str-file-td input:file').trigger('click');
	  }) */

	//generate dashdb input score table list
	$(document).on('change', '#dashdb-model-input-schema', function () {
	  $("#dashdb-model-input-table option:not(:first-child)").remove();
	  var selected_schema = $("#dashdb-model-input-schema option:selected" ).text();
	  var url;
	  if (selected_schema == 'Samples') {
	    url = "http://"+document.location.host+"/tables?sample=true&access_key="+access_key
	  }
	  else {
	    url = "http://"+document.location.host+"/tables?sample=false&access_key="+access_key
	  }

	  $.ajax({
	    type: "GET",
	    url: url,
	    success: function (data) {
	      $("#dashdb-model-input-table option:first").after(data);
	      var table_chosen = $("#dashdb-model-input-table option:nth-child(2)").val();
	      dashdb_model_target_primary_key_autofill(table_chosen);
	      },
      error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            }
	  });

	});



	function dashdb_model_target_primary_key_autofill (table) {
	  $("#dashdb-model-input-primary-key option:not(:first-child)").remove();
	  $("#dashdb-model-input-target-column option:not(:first-child)").remove();
	    console.log(table);
	    $.ajax({
	      type: "GET",
	      url: "http://"+document.location.host+"/columns?table="+table+"&access_key="+access_key,
	      success: function (data) {
	        $("#dashdb-model-input-primary-key option:first").after(data);
	        $("#dashdb-model-input-target-column option:first").after(data);
	       },
        error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            }
	    });  
	}

	//dynamically display table when refresh
	 $(document).on('change', '#dashdb-model-input-table', function () {
	   var table_name =$("#dashdb-model-input-table option:selected" ).text();
	   console.log(table_name);
	   var table = '<div class="dashdb-input-table-area"><table class="score-table" id="dashdb-model-input" hidden><thead><tr></tr></thead><tbody><tr></tr></tbody></table></div>'
	   $('#dashdb-model-input-wrapper').html(table);
	   
	 $.ajax({
	     type: "GET",
	     url: "http://"+document.location.host+"/columns?table="+table_name+"&header=true&access_key="+access_key,
	     success: function(data){
	          $('#dashdb-model-input thead tr').html(data);
	     },
      error: function(jqXHR) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
            },
	     complete: function(jqXHR, textStatus) {
	        if (textStatus == 'success') {
	          var dynatable = $('#dashdb-model-input').dynatable({
	              features: {
	                  pushState: false,
	                  search: false,
	              },        
	              table: {
	                  defaultColumnIdStyle: 'lowercase'
	              },
	              dataset: {
	                  perPageDefault: 10,
	                  perPageOptions: [5,10,20],
	              },
	          }).data('dynatable');

	          $.ajax({
	              type: "GET",
	              url: "http://"+document.location.host+"/tables?table="+table_name+"&access_key="+access_key,
	              success: function(data){
	                  dynatable.records.updateFromJson({records: data});
	                  dynatable.records.init();
	                  dynatable.process();
	                  dashdb_model_target_primary_key_autofill(table_name);
	                  $('.dashdb-input-table-area').css('left', '340px');
      		          $('#dashdb-model-input-wrapper #dynatable-record-count-dashdb-model-input').css('left','360px');
	              },
                error: function(jqXHR) {
                  var modal = $('#error-modal');
                  $('#error-modal-message').html(jqXHR.responseText);
                  modal.modal('show')
                },
	              complete: function() {
	              	  $('#dashdb-model-input-wrapper').show();
	                  $('#dashdb-model-input').show();
	              }
	          });   
	        }
	     }
	  });  
	});



	$(document).on('click', "#add-new-dashdb-create-now", function () {
		$(this).addClass('operating');
		$('#add-new-model-alert').remove();
      var selected_schema = $("#dashdb-model-input-schema option:selected" ).text();
        var schema;
        if (selected_schema == 'Samples') {
            schema = 'SAMPLES'
        }
        var model_data = {
          "schema": schema,
            "input_table" : $("#dashdb-model-input-table").val(),
            "target_column" :  $("#dashdb-model-input-target-column").val(),
            "primary_key" :  $("#dashdb-model-input-primary-key").val()
        }
        $(this).html('Refreshing...');
        var model_name =  $('#current-page-model option:selected').text()
        console.log(model_name)
        $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+model_name+"?response_type=html&access_key="+access_key,
          data: JSON.stringify(model_data),
          success: function (data) {
            $('#add-new-dashdb-create-now').html('Refresh Now');
            $('#error-modal').after(data);
          },
          error: function (jqXHR, status) {
            $('#add-new-dashdb-create-now').html('Refresh Now');
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
          },  
          complete: function () {
          	var modal = $('#add-new-model-alert');
			modal.modal('show');
			$('#add-new-dashdb-create-now').removeClass('operating');
          }
        });
	})

	//API Section
	$('#api-li').click(function () {
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 			var model_name = $('#current-page-model option:selected').text();
 			url = "http://"+document.location.host+"/api/"+model_name+"/swagger?access_key="+access_key;
	        $(function () {
	          var swaggerUi = new SwaggerUi({
	          url: url,
	          dom_id:"swagger-ui-container",
	          validatorUrl: null
	          });
	  
	        swaggerUi.load();
	       });
 		});
 	});

 	//Visualize Section
 	$('#visualization-li').click(function () {
 		console.log('visualization clicked')
 		$(this).siblings('.active').removeClass('active');
 		$(this).addClass('active');
 		jump_to($(this).data('location'), function () {
 		});
 	});

 	$(document).on('click', "#visualize-now", function () {
 		$(this).addClass('operating');
 		$(this).html('Visualizing...');
 		var  model_name = $('#current-page-model option:selected').text();
        $.ajax({
          type: "GET",
          url:"http://"+document.location.host+"/api/"+model_name+"/visualize?access_key="+access_key,
          success: function (data) {
            show_image('./outputs/'+data.username+model_name+'.jpg', 600, 600, "visualization result");
            $("#no-pic-alert").hide();
            $('#visualization-pic').show()
          },
          error: function (jqXHR, status) {
              var modal = $('#error-modal');
              $('#error-modal-message').html(jqXHR.responseText);
              modal.modal('show')
          }, 
          complete: function () {
          	$('#visualize-now').removeClass('operating');
 			$('#visualize-now').html('Visualize Now');
          }
        });
    });
    
    function show_image(src, width, height, alt) {
        var img = document.createElement("img");
        img.src = src;
        img.width = width;
        img.height = height;
        img.alt = alt;
        $("#visualization-pic").html(img); 
        console.log(img)
    }

    /* Real-Time-Score */
        function validated_input (selector) {
        var values = [];
        $(selector).each(function () {
                var ph = $(this).attr('placeholder');
                if (ph == 'SMALLINT' ||
                    ph == 'INTEGER'||
                    ph == 'BIGINT'||
                    ph == 'DECIMAL'||
                    ph == 'REAL'||
                    ph == 'DOUBLE'||
                    ph == 'FLOAT') {
                var value =  +$(this).val();
                values.push(value);
                }
                else {
                var value =  $(this).val();
                values.push(value)
                }
        });
        return values
    }
    

 })
