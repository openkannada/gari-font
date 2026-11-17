VERSION=1.300
default:
	./generate.pe Gari.sfd && echo "Gari.ttf file generated, copy to ~/.fonts/ and run fc-cache"
fedora:
	rm -rf /tmp/gari-ttf-${VERSION}
	mkdir /tmp/gari-ttf-${VERSION}
	cp ChangeLog OFL.txt Gari.ttf README /tmp/gari-ttf-${VERSION}/

	rm -rf /tmp/gari-${VERSION}
	mkdir /tmp/gari-${VERSION}
	cp ChangeLog OFL.txt Gari.sfd generate.pe README /tmp/gari-${VERSION}/
	cp fedora_makefile /tmp/gari-${VERSION}/Makefile

	cd /tmp/; \
	tar -cvzf gari-ttf-${VERSION}.tar.gz gari-ttf-${VERSION}/; \
	tar -cvzf gari-${VERSION}.tar.gz gari-${VERSION}/; \
	rm -rf gari-ttf-${VERSION}; \
	rm -rf gari-${VERSION}; 
clean:
	rm -rf /tmp/gari-ttf-${VERSION}
	rm -rf /tmp/gari-${VERSION}
	rm -rf /tmp/gari-ttf-${VERSION}.tar.gz
	rm -rf /tmp/gari-${VERSION}.tar.gz
