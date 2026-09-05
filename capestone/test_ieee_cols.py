import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.section import WD_SECTION

doc = docx.Document()
doc.add_heading('Title Spanning One Column', 0)
doc.add_paragraph('Author name here')

# Add continuous section break for 2 columns
new_section = doc.add_section(WD_SECTION.CONTINUOUS)
sectPr = new_section._sectPr
cols = sectPr.xpath('./w:cols')[0] if sectPr.xpath('./w:cols') else OxmlElement('w:cols')
cols.set(qn('w:num'), '2')
cols.set(qn('w:space'), '240')
if not sectPr.xpath('./w:cols'):
    sectPr.append(cols)

for i in range(20):
    doc.add_paragraph('This is paragraph ' + str(i) + ' that should be in two columns. ' * 10)

doc.save('/home/ashborn/Documents/capestone/test_ieee.docx')
print("Saved")
