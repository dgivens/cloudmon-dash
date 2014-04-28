$( document ).ready( function()
{
  var refresh_alerts = setInterval(
  function ()
  {
    $.getJSON( '/alarms', function( data )
    {
      // Remove cleared alerts
      $.each( $( "#alarms > tbody > tr" ), function( row )
      {
        var keep = false;
        $.each( data['alarms'], function( index, element )
        {
          if ( row.id == element._id['$oid'] )
          {
            keep = true;
          }
        });
        if ( keep == false )
        {
          $( this ).remove();
        }
      });

      // Push new alarms to top
      var items = [];
      $.each( data['alarms'], function( index, element )
      {
        if ( $( "#" + element._id['$oid'] ).length == 0 )
        {
          var row = "<tr id='" + element._id['$oid'] + "'>";
          row += "<td><span class='label label-" + element.state_label + "'>" + element.state + "</span></td>";
          row += "<td>" + element.hostname + "</td>";
          row += "<td>" + element.check + "</td>";
          row += "<td>" + element.alarm + "</td>";
          row += "<td>" + element.status + "</td>";
          row += "<td>" + element.timestamp + "</td>";
          if ( element.acknowledged == true )
          {
            row += "<td>Yes</td>"
          } else {
            row += "<td>No</td>"
          }
          row += "<td><a href='/alarms/" + element._id['$oid'] + "/acknowledge' title='Acknowledge'><span class='glyphicon glyphicon-ok'></span></a> <a href='/alarms/" + element._id['$oid'] + "/clear' title='Clear'><span class='glyphicon glyphicon-remove'></span></a></td>"
          row += "</tr>";
          items.push(row);
        }
      });
      $( "#alarms > tbody" ).prepend( items.join("\n") );
    });
    $.getJSON( '/events', function( data )
    {
      var table=[];
      $.each( data['events'], function( index, element )
      {
        var row = "<tr>";
        row += "<td><span class='label label-" + element.details.state_label + "'>" + element.details.state + "</span></td>";
        row += "<td>" + element.entity.label + "</td>";
        row += "<td>" + element.check.label + "</td>";
        row += "<td>" + element.alarm.label + "</td>";
        row += "<td>" + element.details.status + "</td>";
        row += "<td>" + element.details.timestamp + "</td>";
        table.push(row)
      });
      $( "#events > tbody").replaceWith( table.join("\n") );
    });
  }, 10000)
});
