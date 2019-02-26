// Poll form on sumbit handler
$('form[name=myForm]').on('submit', function(event){
    event.preventDefault();
    update_poll($(this), this.id);
});

// AJAX for updating poll
function update_poll($obj, idPoll) {
    var csrftoken = $obj.serializeArray()[0]["value"];
    var answer = $obj.serializeArray()[1]["value"];
    var title = $obj.find("label.statement").text();

    $.ajax({
        url:  window.location.pathname + `poll/${answer}/${idPoll}`,
        type:  'POST',
        headers:{
            "X-CSRFToken": csrftoken
        },
        dataType:  'json',

        success:  function (json) {
            var myConfig = {
                "type": "area",
                "scale-x":{
                  "labels":["Совершенно\nсогласен","Скорее\nсогласен",
                  "Отношусь\nнейтрально","Скорее\nне согласен","Абсолютно\nне согласен"],
                  "step":"1",
                },
                "scale-y":{
                "visible":"false",
                },
                "plot":{
                  "aspect":"spline",
                  "line-color": "gray",
                  "marker": {
                    "background-color": "gray",
                  }
                 },
                "tooltip":{
                  "visible":"false",
                },
                "backgroundColor":"#fff",
                "plotarea":{
                  "margin-top":"10",
                  "margin-bottom":"70",
                  "x":"50",
                  "backgroundColor":"#fff",
                },
                "gui": {
                  "contextMenu": {
                    "button": {
                      "visible": "false"
                    }
                  }
                },
                "title": {
                  "text": title,
                  "font-size": 15,
                  "bold":false,
                  "italic":true,
                  "wrap-text":true,
                  "text-align": "left",
                  "adjust-layout":"true",
                 "width":"92%",
                  "x":"4%",
              
                      },
                "series": [
                  {
                    "alphaArea":"0.5",
                    "values": json.values,
                    "gradient-colors":"#00FF00 #7FFF00 #FFFF00 #FFFF00 #FF0000",
                    "gradient-stops":"0.1 0.2 0.4 0.6 0.9",
                    "fill-angle":15,
                  }
                ]
              };
            $obj.replaceWith('<p></p>' + '<div id="myChart' + idPoll + '"></div>')
            zingchart.render({
                id : 'myChart' + idPoll,
                data : myConfig,
                height: 250,
                width: "100%"
            });
        }
    });
};