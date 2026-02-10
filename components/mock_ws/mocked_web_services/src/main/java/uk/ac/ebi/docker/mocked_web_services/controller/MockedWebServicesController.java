package uk.ac.ebi.docker.mocked_web_services.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;

import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import java.io.IOException;
import java.io.StringReader;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@RequestMapping("/")
@RestController
public class MockedWebServicesController {
    public static final Map<String, String> enaHoldDateMap = new HashMap<>();

    public MockedWebServicesController() {
    }

    /* To get a mocked hold date value for a projectAlias*/
    @PostMapping(value = "mocked_ena/mocked_hold_date/", consumes = MediaType.MULTIPART_FORM_DATA_VALUE, produces = "application/xml")
    public ResponseEntity<?> getMockedENAHoldDate(@RequestPart("SUBMISSION") MultipartFile xmlFile) {
        String projectAlias = getProjectAliasFromRequest(xmlFile);

        if (projectAlias == null) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("Could not get project alias from input xml");
        }

        if (enaHoldDateMap.containsKey(projectAlias)) {
            return ResponseEntity.status(HttpStatus.CREATED).body(getENAHoldTemplateXMLWithDate(projectAlias, enaHoldDateMap.get(projectAlias)));
        } else {
            String holdDate = java.time.OffsetDateTime.now()
                    .plusDays(10)
                    .withOffsetSameInstant(java.time.ZoneOffset.UTC)
                    .format(java.time.format.DateTimeFormatter.ofPattern("yyyy-MM-ddZ"));
            return ResponseEntity.status(HttpStatus.CREATED).body(getENAHoldTemplateXMLWithDate(projectAlias, holdDate));
        }
    }

    /* To set a mocked hold date value for a projectAlias*/
    @PutMapping(value = "mocked_ena/mocked_hold_date/", produces = "application/xml")
    public ResponseEntity<?> setMockedENAHoldDate(@RequestBody String xmlRequest) {
        try {
            Document doc = DocumentBuilderFactory.newInstance()
                    .newDocumentBuilder()
                    .parse(new InputSource(new StringReader(xmlRequest)));

            String projectAlias = doc.getElementsByTagName("PROJECT").item(0).getAttributes().getNamedItem("alias").getNodeValue();
            String hold_date = doc.getElementsByTagName("PROJECT").item(0).getAttributes().getNamedItem("holdUntilDate").getNodeValue();

            enaHoldDateMap.put(projectAlias, hold_date);
            return ResponseEntity.ok().build();

        } catch (ParserConfigurationException | IOException | SAXException pe) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(pe.toString());
        }

    }

    /* To delete a mocked hold date value for a projectAlias*/
    @DeleteMapping(value = "mocked_ena/mocked_hold_date/")
    public ResponseEntity<?> delMockedENAHoldDate(@RequestBody String projectAlias) {
        enaHoldDateMap.remove(projectAlias);
        return ResponseEntity.ok().build();
    }

    /* To get all mocked hold date values*/
    @GetMapping(value = "mocked_ena/mocked_hold_date/")
    public ResponseEntity<?> getMockedENAHoldDate() {
        return ResponseEntity.ok().body(enaHoldDateMap);
    }


    private String getENAHoldTemplateXMLWithDate(String projectAlias, String hold_date) {
        return String.format("<RECEIPT>" +
                        "<PROJECT accession=\"PRJEB99999\" alias=\"%s\" status=\"PRIVATE\" holdUntilDate=\"%s\"/>" +
                        "</RECEIPT>",
                projectAlias,
                hold_date
        );
    }


    private String getProjectAliasFromRequest(MultipartFile xmlFile) {
        try {
            Document doc = DocumentBuilderFactory.newInstance()
                    .newDocumentBuilder()
                    .parse(xmlFile.getInputStream());

            return doc.getElementsByTagName("RECEIPT").item(0).getAttributes().getNamedItem("target").getNodeValue();

        } catch (ParserConfigurationException | IOException | SAXException pe) {
            return null;
        }
    }


}
