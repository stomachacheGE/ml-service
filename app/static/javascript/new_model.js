
 $(document).ready(function () {
 		var access_key = $('#access-key').data('key');
	    var step = 1;
	    var model_type;
	    var token = $('#access-key').data('key');
	    $(document).on('click', '#add-next', function () {
	    $('#choose-model-type-alert').hide();
	    model_type = $("#choose-model-type").val();
	    console.log(model_type);
	    if (model_type == 'dashdb') {
	      $('#choose-dashdb-input-alert').show();
	    }
	    else {
	      $('#spss-choose-file-alert').show();
	      console.log('spss selected')
	    }
	    $('#add-last').show();
	    $('.add-new-'+model_type+'-step-'+step).hide();
	    step += 1;
	    $('.add-new-'+model_type+'-step-'+step).show();
	    if ((model_type=="spss" && step==2) || (model_type=="dashdb" && step==3)) {
	      $(this).hide();          
	    }
	    console.log(model_type+'-step-'+step)
	  });

	  $(document).on('click', '#add-last', function () {
	    $("#spss-choose-file-info").hide();
	    $('#add-next').show();
	    $('.add-new-'+model_type+'-step-'+step).hide();
	      step -= 1;
	      $('.add-new-'+model_type+'-step-'+step).show();
	      if (step == 1) {
	       $(this).hide();
	       $('#choose-model-type-alert').show();
	       $('#choose-dashdb-input-alert').hide();
	       $('#spss-choose-file-alert').hide();
	       $('#dashdb-model-input-wrapper').html("");

	     }
	      console.log(model_type+'-step-'+step)
	    });

	  $("#choose-str-file-td input:file").change(function (){

	   var fileName = $(this).val().replace("C:\\fakepath\\", "");
	   //fileName.value.replace("C:\\fakepath\\", "");
	   $("#spss-choose-file-info .filename").html(fileName);
	   $("#spss-choose-file-info").fadeIn("slow");
	   $("#spss-choose-file-alert").hide()
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
	      console.log(data);
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
	   var table = '<div class="dashdb-input-table-area" style="left:20px;"><table class="score-table" id="dashdb-model-input" hidden><thead><tr></tr></thead><tbody><tr></tr></tbody></table></div>'
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
	                  $('#dashdb-model-input-wrapper').show();
	                  $('#dashdb-model-input').show();
	                  dashdb_model_target_primary_key_autofill(table_name);
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

	$("#add-new-dashdb-create-now").click(function () {
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
        $(this).html('Creating...');
        var model_name = $('#new-model-name').val().replace(/ /g,"_");
        console.log(model_name)
        $.ajax({
          type: "POST",
          contentType:"application/json; charset=utf-8",
          url:"http://"+document.location.host+"/api/"+model_name+"?response_type=html&access_key="+access_key,
          data: JSON.stringify(model_data),
          success: function (data) {
            $('#add-new-dashdb-create-now').html('Create Now');
            $('#error-modal').after(data);
          },
          error: function (jqXHR, status) {
    		var modal = $('#error-modal');
		    $('#error-modal-message').html(jqXHR.responseText);
		    modal.modal('show')
            $('#add-new-dashdb-create-now').html('Create Now');
          },  
          complete: function () {
          	var modal = $('#add-new-model-alert');
			modal.modal('show');
			$('#add-new-dashdb-create-now').removeClass('operating');
          }
        });
	});

	$('#upload-form').submit(function() {
		$('#add-new-spss-create-now').addClass('operating');
		$('#add-new-model-alert').remove();
        $('#add-new-spss-create-now').html('Creating...');
        var model_name = $('#new-model-name').val().replace(/ /g,"_");
        console.log(model_name);

	    // submit the form 
	    $('#upload-form').ajaxSubmit({
	        url: "http://"+document.location.host+"/api/"+model_name+"?response_type=html&access_key="+access_key,
	          success: function (data) {
	            $('#add-new-spss-create-now').html('Create Now');
	            $('#error-modal').after(data);
	          },
	          error: function (jqXHR, status) {
	    		var modal = $('#error-modal');
			    $('#error-modal-message').html(jqXHR.responseText);
			    modal.modal('show')
	            $('#add-new-spss-create-now').html('Create Now');
	          },  
	          complete: function () {
	          	var modal = $('#add-new-model-alert');
				modal.modal('show');
				$('#add-new-spss-create-now').removeClass('operating');
	          }
	        });
	    
	    // return false to prevent normal browser submit and page navigation 
	    return false; 
	        
	    });
})