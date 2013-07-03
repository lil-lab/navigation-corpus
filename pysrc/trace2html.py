from optparse import OptionParser
import sys
import navigationutils

'''
    Takes trace data and output a nice HTML with links to the images.
'''


if __name__ == '__main__':
    # Parse command line arguments
    parser = OptionParser(usage = 'usage: %prog -g graphics_dir -t traces_file -i instructions_file -m map -d instruction_id -s subject -o output')
    parser.add_option('-t', '--traces', dest = 'traces_file', help = 'Traces file')
    parser.add_option('-i', '--instructions', dest = 'instructions_file', help = 'Instructions file')
    parser.add_option('-g', '--graphics', dest = 'graphics_dir', help = 'Directory containing graphical map files')
    parser.add_option('-m', '--map', dest = 'map_name', help = 'Map name: Jelly0, L0 or Grid0')
    parser.add_option('-s', '--subject', dest = 'subject_id', help = 'Subject ID')
    parser.add_option('-o', '--output', dest = 'output_file', help = 'Output file, default: stdout')
    parser.add_option('-d', '--instruction-id', dest = 'instruction_id', help = 'Instructions ID')
    (options, args) = parser.parse_args()

    # Open output stream
    if options.output_file:
        out = open(options.output_file, 'w')
    else:
        out = sys.stdout

    subject_id = options.subject_id
    map_name = options.map_name
    instruction_id = options.instruction_id

    # Print the HTML header
    out.write('<html>\n<head><title>Follower Trace: %s following %s</title>\n</head>\n' %
              (subject_id, instruction_id))

    #out.write('<iframe name="image_frame" src="" style="float:right;" width="50%" height="50%"><img id="</iframe>\n\n')
    out.write('<div style="width: 50%; float:right; position:relative;">\n')
    out.write('<img id="view_image" src="" style="position:fixed;width:50%;vertical-align:middle;"/>\n')
    out.write('</div>\n')

    out.write('<div style="width: 50%;">\n')

    # Title
    out.write('<h1>Follower Trace: %s following %s</h1>\n' %
              (subject_id, instruction_id))


    # Get the instruction text and print it
    out.write('<p>\n')
    instructions = navigationutils.read_instructions(options.instructions_file)
    instruction_text = '\n'.join(instructions[instruction_id])
    out.write(instruction_text)
    out.write('</p>\n\n')

    # Get the trace
    traces = navigationutils.read_follower(options.traces_file)
    trace = traces[instruction_id]

    # Write stats
    out.write('<ul>\n')
    out.write('\t<li>confidence=%s</li>\n' % (str(trace.trace_stats()['confidence'] if trace.trace_stats().has_key('confidence') else 'NA')))
    out.write('\t<li>directionRating=%s</li>\n' % (str(trace.trace_stats()['directionRating'] if trace.trace_stats().has_key('directionRating') else 'NA')))
    out.write('\t<li>targetFound=%s</li>\n' % (str(trace.trace_stats()['targetFound'] if trace.trace_stats().has_key('targetFound') else 'NA')))
    out.write('</ul>\n')

    # Get the motions and positions trace and zip them together to print
    out.write('<table border="0">')
    for path_step in trace.path():
        out.write('<tr>')
        # Compose the name of the graphic file
        jpg_filename = '%s/Direction%s_%s_%s_%s.jpg' % (options.graphics_dir, map_name, path_step.x(), path_step.y(), path_step.direction())
        out.write('<td><a href="#" onclick=\'document.getElementById("view_image").src="%s";return false;\'>(%s,%s,%s)</a></td><td>%s</td>\n' % (jpg_filename, path_step.x(), path_step.y(), path_step.direction(), path_step.act()))
        out.write('</tr>\n')
    out.write('</table>\n')
    out.write('</div>\n')

    # Print the HTML footer
    out.write('</html>')

    # Close output stream
    out.close()


